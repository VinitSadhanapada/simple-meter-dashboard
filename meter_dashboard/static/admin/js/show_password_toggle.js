document.addEventListener('DOMContentLoaded', function() {
    var pwd = document.querySelector('input[name=ssh_password]');
    if (pwd) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.innerText = 'Show';
        btn.style.marginLeft = '8px';
        btn.onclick = function(e) {
            e.preventDefault();
            if (pwd.type === 'password') {
                pwd.type = 'text';
                btn.innerText = 'Hide';
            } else {
                pwd.type = 'password';
                btn.innerText = 'Show';
            }
        };
        pwd.parentNode.appendChild(btn);
    }
});
