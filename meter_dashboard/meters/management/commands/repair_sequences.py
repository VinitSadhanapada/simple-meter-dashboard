from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


EXPLICIT_SYSTEM_SEQUENCES = [
    # Django admin log table
    ("django_admin_log_id_seq", "django_admin_log"),
    # Migrations history
    ("django_migrations_id_seq", "django_migrations"),
]


class Command(BaseCommand):
    help = "Reset Postgres sequences to max(id) for all Django models with integer AutoFields, and for key Django system tables."

    def _quote(self, name: str):
        return connection.ops.quote_name(name)

    def _reset_for_model(self, model) -> None:
        meta = model._meta
        pk = meta.pk
        # Only for integer-based autoincrement fields
        if pk is None:
            return
        internal = getattr(pk, 'get_internal_type', lambda: None)()
        if internal not in ("AutoField", "BigAutoField", "SmallAutoField"):
            return

        table = meta.db_table
        pk_col = pk.column

        # Determine the sequence for this table+pk
        with connection.cursor() as cur:
            try:
                cur.execute("SELECT pg_get_serial_sequence(%s, %s)", [table, pk_col])
                row = cur.fetchone()
                if not row or not row[0]:
                    self.stdout.write(self.style.WARNING(
                        f"No sequence for {table}.{pk_col} (may be identity or custom PK). Skipping."))
                    return
                seq_name = row[0]

                sql = (
                    f"SELECT setval(%s, COALESCE((SELECT MAX({self._quote(pk_col)}) FROM {self._quote(table)}), 1))"
                )
                cur.execute(sql, [seq_name])
                self.stdout.write(self.style.SUCCESS(
                    f"Reset sequence {seq_name} based on {table}.{pk_col}."))
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Could not reset sequence for model {model.__name__}: {e}"))

    def handle(self, *args, **kwargs):
        # 1) Reset for all models
        for model in apps.get_models():
            self._reset_for_model(model)

        # 2) Explicitly reset a couple of system tables usually not covered above
        with connection.cursor() as cur:
            for seq_name, table_name in EXPLICIT_SYSTEM_SEQUENCES:
                try:
                    sql = (
                        f"SELECT setval(%s, COALESCE((SELECT MAX(id) FROM {self._quote(table_name)}), 1))"
                    )
                    cur.execute(sql, [seq_name])
                    self.stdout.write(self.style.SUCCESS(
                        f"Reset sequence {seq_name} based on {table_name}."))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"Could not reset sequence {seq_name}: {e}"))
