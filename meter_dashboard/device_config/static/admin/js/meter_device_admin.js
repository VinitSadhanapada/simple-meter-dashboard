// Enhanced meter model input with autocomplete functionality
(function ($) {
    $(document).ready(function () {
        const meterModelField = $('#id_meter_model');

        if (meterModelField.length) {
            // Create suggestions container
            const suggestionsContainer = $('<div class="meter-model-suggestions"></div>');
            meterModelField.parent().append(suggestionsContainer);

            // Add help text with legend
            const helpText = $(`
                <div class="meter-models-legend">
                    <div class="legend-item">
                        <span class="legend-predefined">● Predefined Models:</span> 
                        Common meter models (LG6400, LG+5220, etc.)
                    </div>
                    <div class="legend-item">
                        <span class="legend-custom">● Custom Models:</span> 
                        Previously entered custom models
                    </div>
                    <div class="legend-item">
                        <strong>Tip:</strong> Start typing to see suggestions, or enter a new model name.
                    </div>
                </div>
            `);
            meterModelField.parent().append(helpText);

            // Predefined models (will be populated from backend)
            let predefinedModels = [
                'LG6400', 'LG+5220', 'LG+5310', 'LG+5230', 'LG+5240', 'LG+5250'
            ];

            // Get custom models from existing data (simulated - in real scenario this would come from backend)
            let customModels = [];

            // All available models
            let allModels = [...predefinedModels, ...customModels];

            // Filter and show suggestions
            function showSuggestions(query) {
                const filtered = allModels.filter(model =>
                    model.toLowerCase().includes(query.toLowerCase())
                );

                suggestionsContainer.empty();

                if (filtered.length > 0 && query.length > 0) {
                    filtered.forEach(model => {
                        const isPredefined = predefinedModels.includes(model);
                        const suggestion = $(`
                            <div class="meter-model-suggestion ${isPredefined ? 'predefined' : 'custom'}" 
                                 data-model="${model}">
                                ${model} ${isPredefined ? '(Predefined)' : '(Custom)'}
                            </div>
                        `);

                        suggestion.click(function () {
                            meterModelField.val(model);
                            suggestionsContainer.hide();
                        });

                        suggestionsContainer.append(suggestion);
                    });

                    suggestionsContainer.show();
                } else {
                    suggestionsContainer.hide();
                }
            }

            // Event handlers
            meterModelField.on('input', function () {
                const query = $(this).val();
                showSuggestions(query);
            });

            meterModelField.on('focus', function () {
                const query = $(this).val();
                showSuggestions(query);
            });

            // Hide suggestions when clicking outside
            $(document).click(function (e) {
                if (!$(e.target).closest('.field-meter_model').length) {
                    suggestionsContainer.hide();
                }
            });

            // Validation feedback
            meterModelField.on('blur', function () {
                const value = $(this).val().trim();
                if (value) {
                    if (!allModels.includes(value)) {
                        // This is a new custom model
                        const feedback = $('<div class="meter-model-feedback" style="color: #1976d2; font-size: 12px; margin-top: 5px;">New model "' + value + '" will be added to available options.</div>');
                        meterModelField.parent().find('.meter-model-feedback').remove();
                        meterModelField.parent().append(feedback);

                        // Add to custom models for future suggestions
                        if (!customModels.includes(value)) {
                            customModels.push(value);
                            allModels.push(value);
                        }
                    } else {
                        meterModelField.parent().find('.meter-model-feedback').remove();
                    }
                }
                suggestionsContainer.hide();
            });

            // Add validation on form submit
            $('form').on('submit', function () {
                const value = meterModelField.val().trim();
                if (!value) {
                    alert('Please enter a meter model.');
                    meterModelField.focus();
                    return false;
                }
            });
        }
    });
})(django.jQuery);
