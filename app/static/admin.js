document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('admin-sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (toggle && sidebar && overlay) {
        toggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('visible');
        });

        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('visible');
        });
    }
});

/**
 * Chip Input Component
 * Handles creating chips from text input
 */
class ChipInput {
    constructor(containerId, inputId, hiddenInputId) {
        this.container = document.getElementById(containerId);
        this.input = document.getElementById(inputId);
        this.hiddenInput = document.getElementById(hiddenInputId);
        
        if (!this.container || !this.input || !this.hiddenInput) return;

        this.chips = [];
        this.init();
    }

    init() {
        // Load initial values
        const initialVal = this.hiddenInput.value;
        if (initialVal) {
            this.chips = initialVal.split(',').map(s => s.trim()).filter(s => s);
        }
        this.render();

        // Events
        this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.input.addEventListener('blur', () => this.addChip(this.input.value)); // Add on blur
        
        // Focus container -> Focus input
        this.container.addEventListener('click', (e) => {
            if (e.target === this.container) {
                this.input.focus();
            }
        });

        // Float label logic helper
        this.input.addEventListener('focus', () => {
            this.container.classList.add('focused');
        });
        this.input.addEventListener('blur', () => {
            this.container.classList.remove('focused');
        });
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            this.addChip(this.input.value);
        } else if (e.key === 'Backspace' && this.input.value === '' && this.chips.length > 0) {
            this.removeChip(this.chips.length - 1);
        }
    }

    addChip(text) {
        const val = text.trim().replace(/,/g, '');
        if (!val) return;
        
        if (!this.chips.includes(val)) {
            this.chips.push(val);
            this.update();
        }
        this.input.value = '';
    }

    removeChip(index) {
        this.chips.splice(index, 1);
        this.update();
    }

    setValue(valueString) {
        this.hiddenInput.value = valueString || "";
        if (this.hiddenInput.value) {
            this.chips = this.hiddenInput.value.split(',').map(s => s.trim()).filter(s => s);
        } else {
            this.chips = [];
        }
        this.render();
    }

    update() {
        this.hiddenInput.value = this.chips.join(',');
        this.render();
    }

    render() {
        // Remove existing chips (but keep input and label)
        // We know input and label are compliant to MD3 structure
        // But simpler to just remove chips elements we added
        
        // Find existing chips
        const existingChips = this.container.querySelectorAll('.edit-chip');
        existingChips.forEach(el => el.remove());

        // Insert before input
        this.chips.forEach((chipText, index) => {
            const chip = document.createElement('span');
            chip.className = 'edit-chip';
            chip.innerHTML = `
                ${chipText}
                <span class="material-symbols-outlined">close</span>
            `;
            
            // Delete event
            chip.querySelector('.material-symbols-outlined').addEventListener('click', (e) => {
                e.stopPropagation(); // prevent container focus
                this.removeChip(index);
            });

            this.container.insertBefore(chip, this.input);
        });

        // Toggle class for label floating
        if (this.chips.length > 0) {
            this.container.classList.add('has-chips');
        } else {
            this.container.classList.remove('has-chips');
        }
    }
}

/**
 * Tag Picker Logic (Modal-based)
 * Replaces ChipInput for Styles/Colors
 */
/**
 * Tag Picker Logic (Modal-based)
 * Replaces ChipInput for Styles/Colors
 * Requires: #picker-overlay in HTML
 */
class TagPicker {
    constructor(containerId, hiddenInputId, type, options = []) {
        this.container = document.getElementById(containerId);
        this.hiddenInput = document.getElementById(hiddenInputId);
        this.type = type; // 'styles' or 'colors'
        this.options = options || [];
        
        if (!this.container || !this.hiddenInput) return;

        this.init();
    }

    init() {
        this.render();
        
        // Add "+ ADD" button logic
        // We will append a button to container if not exists, or bind existing?
        // Let's clear container and rebuild to be safe and consistent.
        // Or expects container to be the display wrapper?
        // In item_edit.html: .tag-display is the container.
        // Let's stick to that pattern.
    }

    setValue(valueString) {
        this.hiddenInput.value = valueString || "";
        this.render();
    }

    render() {
        this.container.innerHTML = '';
        const values = this.hiddenInput.value ? this.hiddenInput.value.split(',').map(s => s.trim()).filter(s => s) : [];
        
        // Render Chips
        values.forEach(v => {
            const chip = document.createElement('span');
            chip.className = 'chip'; // Updated to match admin/items style (from edit-chip)
            chip.textContent = v;
            
            const removeBtn = document.createElement("span");
            removeBtn.className = "chip-remove"; // Updated to match admin/items style (from material-symbols + text)
            removeBtn.textContent = "×"; // Simple text x instead of icon to match CSS .chip-remove
            removeBtn.onclick = (e) => {
                e.stopPropagation();
                this.removeValue(v);
            };

            chip.appendChild(removeBtn);
            this.container.appendChild(chip);
        });

        // Add Button
        const addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.className = 'btn-add'; // From admin.css
        // Removed inline marginLeft - container has gap: 8px
        addBtn.textContent = '+ ADD';
        addBtn.onclick = () => this.openPickerModal();
        
        this.container.appendChild(addBtn);
    }

    removeValue(val) {
        let values = this.hiddenInput.value ? this.hiddenInput.value.split(',') : [];
        values = values.filter(v => v !== val);
        this.hiddenInput.value = values.join(',');
        this.render();
    }

    openPickerModal() {
        const modal = document.getElementById('picker-overlay');
        const grid = document.getElementById('tag-grid'); // Fixed ID from item_edit.html pattern
        const title = document.getElementById('modal-title');
        const applyBtn = document.getElementById('modal-apply');
        
        if (!modal) {
            console.error('Picker modal markup not found (#picker-overlay)');
            return;
        }
        
        // Determine Options
        // If type is styles, we might need to fetch from global or passed options
        let options = this.options;
        if (this.type === 'styles' && (!options || options.length === 0)) {
            // Try global
            if (window.AVAILABLE_STYLES) options = window.AVAILABLE_STYLES;
        }
        if (this.type === 'colors' && (!options || options.length === 0)) {
             options = ["黒", "白", "グレー", "ネイビー", "青", "ベージュ", "ブラウン", "緑", "赤"];
        }

        const currentValues = this.hiddenInput.value ? this.hiddenInput.value.split(',').map(s=>s.trim()) : [];
        
        // Setup Modal
        grid.innerHTML = '';
        title.textContent = this.type === 'styles' ? 'SELECT STYLES' : 'SELECT COLORS';
        
        // Render Presets
        options.forEach(opt => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'tag-btn' + (currentValues.includes(opt) ? ' active' : '');
            btn.textContent = opt;
            btn.onclick = () => btn.classList.toggle('active');
            grid.appendChild(btn);
        });

        // Other Input (Custom)
        // Filter out presets to find custom ones
        const customVals = currentValues.filter(v => !options.includes(v));
        
        const otherBtn = document.createElement("button");
        otherBtn.type = "button";
        otherBtn.className = "tag-btn other-trigger";
        otherBtn.textContent = "+ OTHER";
        otherBtn.style.borderStyle = "dashed";

        const otherInput = document.createElement("input");
        otherInput.type = "text";
        otherInput.className = "tag-input"; // Check admin.css if exists, else inline style
        otherInput.style.display = "none";
        otherInput.style.padding = "8px";
        otherInput.style.border = "1px solid #ddd";
        otherInput.style.borderRadius = "4px";
        otherInput.placeholder = "タグを入力";
        otherInput.value = customVals.join(',');

        const showInput = () => { otherBtn.style.display = "none"; otherInput.style.display = "inline-block"; otherInput.focus(); };
        const showBtn = () => { otherBtn.style.display = "inline-block"; otherInput.style.display = "none"; };
        
        otherBtn.onclick = () => showInput();
        otherInput.onblur = () => { if (!otherInput.value.trim()) showBtn(); };
        
        if (customVals.length > 0) showInput(); else showBtn();

        grid.appendChild(otherBtn);
        grid.appendChild(otherInput);

        // Show
        modal.classList.remove('hidden');

        // Apply Handler
        // Remove old listeners to avoid stacking? 
        // Simplest is to overwrite onclick or use a distinct function reference if possible. 
        // Or cloneNode to strip listeners.
        // NOTE: We should be careful about replacing elements if other event listeners exist.
        // But here we need to ensure fresh closure context.
        const newApplyBtn = applyBtn.cloneNode(true);
        applyBtn.parentNode.replaceChild(newApplyBtn, applyBtn);
        
        newApplyBtn.onclick = () => {
             // Gather Presets
            const selectedPresets = Array.from(grid.querySelectorAll('.tag-btn.active:not(.other-trigger)')).map(b => b.textContent);
            
            // Gather Custom
            const otherText = otherInput.value.trim();
            const customTags = otherText ? otherText.split(',').map(s=>s.trim()).filter(Boolean) : [];
            
            const finalSet = new Set([...selectedPresets, ...customTags]);
            this.hiddenInput.value = Array.from(finalSet).join(',');
            this.render();
            
            modal.classList.add('hidden');
        };

        // Close on Escape logic is handled globally or add here?
        // Add simple close handler on overlay click is usually in HTML or global init.
        // Let's add simple one here for safety if not exists.
        modal.onclick = (e) => {
            if (e.target === modal) modal.classList.add('hidden');
        };
    }
}
