// ====== STATE MANAGEMENT & APP INITIALIZATION ======
class TaskTrackerApp {
    constructor() {
        this.state = {
            tasks: [],
            favorites: [],
            taskLog: {},
            currentWorkingTask: null,
            allDone: false,
            deadline: null,
            deadlineDisplay: null,
            videoVisible: localStorage.getItem('videoVisible') === 'true',
            theme: localStorage.getItem('theme') || 'light'
        };
        
        this.elements = {};
        this.timers = {};
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.cacheElements();
        this.initializeTheme();
        this.initializeVideo();
        this.initializeEventListeners();
        this.startTimers();
        
        // Initialize focus mode if active
        if (window.focusMode) {
            this.initFocusMode();
            return;
        }
        
        // Load initial data
        this.loadTasks();
        this.loadInitialDeadlineIncrements();
    }
    
    cacheElements() {
        try {
            this.elements = {
                // Main elements
                body: document.body,
                countdown: document.getElementById('countdown'),
                spentTime: document.getElementById('spent-time'),
                
                // Video elements
                videoToggleBtn: document.getElementById('toggle-video'),
                videoContainer: document.getElementById('video-container'),
                
                // Theme elements
                themeSwitch: document.getElementById('theme-switch'),
                
                // Form elements
                taskForm: document.querySelector('form[action*="/add"]'),
                taskInput: document.querySelector('input[name="task_text"]'),
                favoriteForm: document.querySelector('form[action*="/add_favorite"]'),
                favoriteInput: document.querySelector('input[name="favorite_text"]'),
                deadlineForm: document.querySelector('form[action*="/set_deadline"]'),
                
                // Tables and containers
                taskTable: document.querySelector('.task-table tbody'),
                favoritesTable: document.querySelector('.task-table:last-of-type tbody'),
                logTable: document.querySelectorAll('.task-table')[1]?.querySelector('tbody'),
                
                // Headers and displays
                deadlineDisplay: document.querySelector('.deadline-display'),
                currentTaskDisplay: document.querySelector('.currenttask-display'),
                
                // Loading overlay (we'll create this)
                loadingOverlay: null
            };
            
            // Validate critical elements exist
            const criticalElements = ['body', 'themeSwitch'];
            const missingElements = criticalElements.filter(key => !this.elements[key]);
            
            if (missingElements.length > 0) {
                console.warn('Missing critical elements:', missingElements);
            }
            
            this.createLoadingOverlay();
            console.log('Elements cached successfully');
        } catch (error) {
            console.error('Error caching elements:', error);
            this.showError('Failed to initialize application');
        }
    }
    
    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <div class="loading-text">Updating...</div>
            </div>
        `;
        document.body.appendChild(overlay);
        this.elements.loadingOverlay = overlay;
    }
    
    showLoading() {
        this.isLoading = true;
        this.elements.loadingOverlay.classList.add('visible');
    }
    
    hideLoading() {
        this.isLoading = false;
        this.elements.loadingOverlay.classList.remove('visible');
    }
    
    // ====== THEME MANAGEMENT ======
    initializeTheme() {
        if (!this.elements.themeSwitch) return;
        
        // Ensure both documentElement and body have the same theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.state.theme = savedTheme;
        
        // Apply theme to both elements consistently
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.elements.body.setAttribute('data-theme', savedTheme);
        
        // Set switch state
        this.elements.themeSwitch.checked = savedTheme === 'dark';
        
        // Theme switch event listener with robust handling
        this.elements.themeSwitch.addEventListener('change', (e) => {
            try {
                const newTheme = e.target.checked ? 'dark' : 'light';
                this.state.theme = newTheme;
                
                // Apply to both elements
                document.documentElement.setAttribute('data-theme', newTheme);
                this.elements.body.setAttribute('data-theme', newTheme);
                
                // Save to localStorage
                localStorage.setItem('theme', newTheme);
                
                console.log(`Theme switched to: ${newTheme}`);
            } catch (error) {
                console.error('Error switching theme:', error);
                this.showError('Failed to switch theme');
            }
        });
        
        console.log(`Theme initialized: ${savedTheme}`);
    }
    
    // ====== VIDEO MANAGEMENT ======
    initializeVideo() {
        if (!this.elements.videoToggleBtn || !this.elements.videoContainer) return;
        
        // Apply initial state
        if (!this.state.videoVisible) {
            this.elements.videoContainer.classList.add('hidden');
            this.elements.videoToggleBtn.textContent = 'Show Video';
        } else {
            this.elements.videoToggleBtn.textContent = 'Hide Video';
        }
        
        this.elements.videoToggleBtn.addEventListener('click', () => {
            this.toggleVideo();
        });
    }
    
    toggleVideo() {
        this.state.videoVisible = !this.state.videoVisible;
        localStorage.setItem('videoVisible', this.state.videoVisible);
        
        if (this.state.videoVisible) {
            this.elements.videoContainer.classList.remove('hidden');
            this.elements.videoToggleBtn.textContent = 'Hide Video';
        } else {
            this.elements.videoContainer.classList.add('hidden');
            this.elements.videoToggleBtn.textContent = 'Show Video';
        }
    }
    
    // ====== EVENT LISTENERS ======
    initializeEventListeners() {
        // Task form submission
        if (this.elements.taskForm) {
            this.elements.taskForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addTask();
            });
        }
        
        // Favorite form submission
        if (this.elements.favoriteForm) {
            this.elements.favoriteForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addFavorite();
            });
        }
        
        // Deadline form submission
        if (this.elements.deadlineForm) {
            this.elements.deadlineForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.setDeadline();
            });
        }
        
        // Global event delegation
        document.addEventListener('click', (e) => this.handleClick(e));
        document.addEventListener('change', (e) => this.handleChange(e));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    handleClick(e) {
        const target = e.target;
        
        // Complete/Uncomplete task
        if (target.closest('.complete-btn')) {
            e.preventDefault();
            this.toggleTaskComplete(target.closest('.complete-btn'));
        }
        
        // Delete task
        else if (target.closest('.delete-btn')) {
            e.preventDefault();
            this.deleteItem(target.closest('.delete-btn'));
        }
        
        // Add from favorites/log
        else if (target.closest('a[href*="add_task_from"]')) {
            e.preventDefault();
            this.addTaskFrom(target.closest('a'));
        }
        
        // Sort buttons
        else if (target.closest('.sort-btn')) {
            e.preventDefault();
            this.sortTasks(target.closest('.sort-btn'));
        }
        
        // Clear tasks
        else if (target.closest('.cleartasks-btn')) {
            e.preventDefault();
            this.clearTasks();
        }
        
        // Reset timer
        else if (target.closest('.reset-btn')) {
            e.preventDefault();
            this.resetTimer();
        }
    }
    
    handleChange(e) {
        const target = e.target;
        
        // Priority updates
        if (target.classList.contains('priority-select')) {
            this.updatePriority(target);
        }
        
        // Deadline updates
        else if (target.classList.contains('deadline-select')) {
            this.updateTaskDeadline(target);
        }
    }
    
    handleKeyboard(e) {
        // Ctrl/Cmd + Enter to quickly add task
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const taskInput = this.elements.taskInput;
            if (taskInput && !taskInput.value.trim()) {
                taskInput.focus();
                e.preventDefault();
            }
        }
        
        // Escape to clear focused input
        if (e.key === 'Escape') {
            const activeElement = document.activeElement;
            if (activeElement && activeElement.tagName === 'INPUT') {
                activeElement.blur();
            }
        }
    }
    
    // ====== API CALLS ======
    async makeRequest(url, options = {}) {
        if (this.isLoading && !options.skipLoading) return null;
        
        if (!options.skipLoading) this.showLoading();
        
        try {
            const defaultOptions = {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            };
            
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();
            
            if (!options.skipLoading) this.hideLoading();
            
            return data;
        } catch (error) {
            console.error('Request failed:', error);
            this.showError('Operation failed. Please try again.');
            if (!options.skipLoading) this.hideLoading();
            return null;
        }
    }
    
    // ====== TASK OPERATIONS ======
    async loadTasks() {
        try {
            const data = await this.makeRequest('/api/tasks');
            
            if (data) {
                this.state.tasks = data.tasks || [];
                this.state.currentWorkingTask = data.current_working_task || null;
                this.state.allDone = data.all_done || false;
                
                // Update global variables for backward compatibility
                window.allDone = this.state.allDone;
                window.deadlineSet = !!(data.task_deadline_increments && this.state.deadline);
                
                this.updateTaskDisplay();
                this.updateCurrentTaskDisplay();
                
                // Initialize task deadline selects with fresh data
                if (data.task_deadline_increments) {
                    this.refreshTaskDeadlineSelects(data.task_deadline_increments);
                }
            }
        } catch (error) {
            console.error('Error loading tasks:', error);
            this.showError('Failed to load tasks');
        }
    }
    
    async addTask() {
        const taskText = this.elements.taskInput.value.trim();
        if (!taskText) return;
        
        const formData = new FormData();
        formData.append('task_text', taskText);
        
        const data = await this.makeRequest('/add', {
            method: 'POST',
            body: formData
        });
        
        if (data && data.success) {
            this.elements.taskInput.value = '';
            this.state.tasks.push(data.task);
            this.addTaskToTable(data.task, data.task_index);
            this.updateCurrentTaskDisplay();
            this.showSuccess('Task added successfully!');
        }
    }
    
    async toggleTaskComplete(button) {
        const url = button.href;
        const data = await this.makeRequest(url);
        
        if (data && data.success) {
            const taskRow = button.closest('tr');
            const taskCell = taskRow.querySelector('.task-cell');
            
            if (data.task.completed) {
                // Add completed class and remove overdue classes
                taskCell.classList.add('task-completed');
                taskCell.classList.remove('task-overdue');
                taskRow.classList.remove('overdue-task');
                
                // Remove overdue styling from countdown if it exists
                const countdownDiv = taskRow.querySelector('.task-countdown');
                if (countdownDiv) {
                    countdownDiv.classList.remove('overdue-text');
                }
                
                button.textContent = 'Undo';
                if (data.lap_time) {
                    const timeCell = taskRow.children[3];
                    timeCell.textContent = data.lap_time;
                }
            } else {
                taskCell.classList.remove('task-completed');
                button.textContent = 'Complete';
                const timeCell = taskRow.children[3];
                timeCell.textContent = '-';
                
                // Re-check if task should be marked as overdue
                const deadlineStr = taskRow.querySelector('.task-countdown')?.getAttribute('data-deadline');
                if (deadlineStr && new Date(deadlineStr) < new Date()) {
                    taskCell.classList.add('task-overdue');
                    taskRow.classList.add('overdue-task');
                    taskRow.querySelector('.task-countdown')?.classList.add('overdue-text');
                }
            }
            
            // Update local state
            const taskIndex = Array.from(taskRow.parentNode.children).indexOf(taskRow);
            if (this.state.tasks[taskIndex]) {
                this.state.tasks[taskIndex] = data.task;
            }
            
            this.updateCurrentTaskDisplay();
            this.showSuccess(data.task.completed ? 'Task completed!' : 'Task unmarked');
        }
    }
    
    async deleteItem(button) {
        const url = button.href;
        const data = await this.makeRequest(url);
        
        if (data && data.success) {
            const row = button.closest('tr');
            this.animateRowRemoval(row);
            
            // Update local state based on the type of deletion
            if (url.includes('/delete/')) {
                // Task deletion
                this.state.tasks.splice(data.task_id, 1);
                this.updateCurrentTaskDisplay();
            } else if (url.includes('/delete_favorite/')) {
                // Favorite deletion
                this.state.favorites = data.favorites;
            } else if (url.includes('/delete_from_log/')) {
                // Log deletion
                this.state.taskLog = data.task_log;
            }
            
            this.showSuccess('Item deleted successfully!');
        }
    }
    
    // ====== UI UPDATES ======
    addTaskToTable(task, index) {
        if (!this.elements.taskTable) return;
        
        const row = this.createTaskRow(task, index);
        this.elements.taskTable.appendChild(row);
        this.animateRowAddition(row);
        
        // Ensure priority select styling is applied
        const prioritySelect = row.querySelector('.priority-select');
        if (prioritySelect) {
            this.updatePrioritySelectBorder(prioritySelect);
        }
    }
    
    createTaskRow(task, index) {
        const row = document.createElement('tr');
        const isOverdue = task.task_deadline && new Date(task.task_deadline) < new Date();
        
        row.className = isOverdue ? 'overdue-task' : '';
        row.innerHTML = `
            <td class="task-cell ${task.completed ? 'task-completed' : ''} ${isOverdue ? 'task-overdue' : ''}">
                ${this.escapeHtml(task.text)}
            </td>
            <td class="priority-cell">
                <form class="inline-form">
                    <select name="priority" class="priority-select">
                        ${[1,2,3,4,5].map(p => 
                            `<option value="${p}" ${(task.priority || 3) === p ? 'selected' : ''}>${p}</option>`
                        ).join('')}
                    </select>
                </form>
            </td>
            <td class="deadline-cell">
                <form class="inline-form">
                    <select name="task_deadline" class="deadline-select">
                        <option value="">No deadline</option>
                        ${this.generateDeadlineOptions(task.task_deadline || '')}
                    </select>
                </form>
                ${task.task_deadline ? `<div class="task-countdown ${isOverdue ? 'overdue-text' : ''}" data-deadline="${task.task_deadline}">--:--</div>` : ''}
            </td>
            <td>${task.lap_time || '-'}</td>
            <td>
                <a href="/complete/${index}" class="btn complete-btn">
                    ${task.completed ? 'Undo' : 'Complete'}
                </a>
            </td>
            <td>
                <a href="/delete/${index}" class="btn delete-btn">X</a>
            </td>
        `;
        
        return row;
    }
    
    updateTaskDisplay() {
        if (!this.elements.taskTable) return;
        
        // Clear existing rows
        this.elements.taskTable.innerHTML = '';
        
        // Add all tasks
        this.state.tasks.forEach((task, index) => {
            const row = this.createTaskRow(task, index);
            this.elements.taskTable.appendChild(row);
        });
        
        this.initializePrioritySelects();
    }
    
    updateCurrentTaskDisplay() {
        if (!this.elements.currentTaskDisplay) return;
        
        const workingTask = this.getCurrentWorkingTask();
        const text = workingTask ? 
            `Time Spent on "${workingTask.text}":` : 
            'No Current Task:';
        
        this.elements.currentTaskDisplay.textContent = text;
    }
    
    getCurrentWorkingTask() {
        const incompleteTasks = this.state.tasks.filter(task => !task.completed);
        if (incompleteTasks.length === 0) return null;
        
        // Sort by priority (lowest number = highest priority)
        incompleteTasks.sort((a, b) => (a.priority || 5) - (b.priority || 5));
        return incompleteTasks[0];
    }
    
    // ====== ANIMATIONS ======
    animateRowAddition(row) {
        row.style.opacity = '0';
        row.style.transform = 'translateY(-20px)';
        row.style.transition = 'all 0.3s ease';
        
        requestAnimationFrame(() => {
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        });
    }
    
    animateRowRemoval(row) {
        row.style.transition = 'all 0.3s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(-100%)';
        
        setTimeout(() => {
            if (row.parentNode) {
                row.parentNode.removeChild(row);
            }
        }, 300);
    }
    
    // ====== NOTIFICATIONS ======
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.classList.add('visible');
        });
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('visible');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    // ====== UTILITY FUNCTIONS ======
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // ====== MISSING METHODS ======
    
    refreshTaskDeadlineSelects(taskDeadlineIncrements) {
        if (!taskDeadlineIncrements) return;
        
        // Store the increments for later use
        this.state.taskDeadlineIncrements = taskDeadlineIncrements;
        
        // Update all existing deadline selects
        const deadlineSelects = document.querySelectorAll('.deadline-select');
        deadlineSelects.forEach(select => {
            const currentValue = select.value;
            
            // Clear existing options except "No deadline"
            select.innerHTML = '<option value="">No deadline</option>';
            
            // Add new options
            taskDeadlineIncrements.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.value;
                optionElement.textContent = option.text;
                if (option.value === currentValue) {
                    optionElement.selected = true;
                }
                select.appendChild(optionElement);
            });
        });
    }
    
    generateDeadlineOptions(selectedValue = '') {
        if (!this.state.taskDeadlineIncrements) {
            // If increments aren't loaded yet, return a placeholder
            // The options will be populated when loadInitialDeadlineIncrements() completes
            return '<!-- Options will be populated when increments are loaded -->';
        }
        
        return this.state.taskDeadlineIncrements.map(option => {
            const selected = option.value === selectedValue ? 'selected' : '';
            return `<option value="${this.escapeHtml(option.value)}" ${selected}>${this.escapeHtml(option.text)}</option>`;
        }).join('');
    }
    
    async loadInitialDeadlineIncrements() {
        try {
            const data = await this.makeRequest('/api/tasks', { skipLoading: true });
            if (data && data.task_deadline_increments) {
                console.log('Loaded task deadline increments:', data.task_deadline_increments.length, 'options');
                this.refreshTaskDeadlineSelects(data.task_deadline_increments);
                
                // Also check if there are any empty deadline dropdowns that need populating
                this.populateEmptyDeadlineDropdowns();
            } else {
                console.warn('No task deadline increments received from server');
            }
        } catch (error) {
            console.error('Error loading deadline increments:', error);
        }
    }
    
    populateEmptyDeadlineDropdowns() {
        // Find any deadline dropdowns that only have the "No deadline" option
        const emptyDropdowns = document.querySelectorAll('.deadline-select');
        emptyDropdowns.forEach(dropdown => {
            if (dropdown.options.length <= 1) {
                // This dropdown needs to be populated
                this.refreshSingleDeadlineSelect(dropdown);
            }
        });
    }
    
    refreshSingleDeadlineSelect(select) {
        if (!this.state.taskDeadlineIncrements || !select) return;
        
        const currentValue = select.value;
        
        // Clear existing options except "No deadline"
        select.innerHTML = '<option value="">No deadline</option>';
        
        // Add new options
        this.state.taskDeadlineIncrements.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.value;
            optionElement.textContent = option.text;
            if (option.value === currentValue) {
                optionElement.selected = true;
            }
            select.appendChild(optionElement);
        });
    }
    
    async addFavorite() {
        const favoriteText = this.elements.favoriteInput.value.trim();
        if (!favoriteText) return;
        
        const formData = new FormData();
        formData.append('favorite_text', favoriteText);
        
        const data = await this.makeRequest('/add_favorite', {
            method: 'POST',
            body: formData
        });
        
        if (data && data.success) {
            this.elements.favoriteInput.value = '';
            this.state.favorites = data.favorites;
            this.showSuccess('Favorite added successfully!');
            // Optionally refresh the favorites table
            this.refreshFavoritesTable();
        } else if (data && data.error) {
            this.showError(data.error);
        }
    }
    
    async setDeadline() {
        const formData = new FormData(this.elements.deadlineForm);
        
        const data = await this.makeRequest('/set_deadline', {
            method: 'POST',
            body: formData
        });
        
        if (data && data.success) {
            this.state.deadline = data.deadline;
            this.state.deadlineDisplay = data.deadline_display;
            
            // CRITICAL FIX: Update the global window variable that timers check
            window.deadlineSet = true;
            
            // Update deadline display - create element if it doesn't exist
            let deadlineDisplay = this.elements.deadlineDisplay;
            if (!deadlineDisplay) {
                // Create deadline display element
                deadlineDisplay = document.createElement('div');
                deadlineDisplay.className = 'deadline-display';
                
                // Insert it before the timer container
                const timerContainer = document.querySelector('.timer-container');
                if (timerContainer && timerContainer.parentNode) {
                    timerContainer.parentNode.insertBefore(deadlineDisplay, timerContainer);
                    this.elements.deadlineDisplay = deadlineDisplay;
                }
            }
            
            if (deadlineDisplay) {
                deadlineDisplay.textContent = `Deadline: ${data.deadline_display}`;
                deadlineDisplay.style.display = 'block';
            }
            
            // Force timer update immediately
            this.updateMainTimers();
            
            this.showSuccess('Countdown started successfully!');
        } else if (data && data.error) {
            this.showError(data.error);
        }
    }
    
    async resetTimer() {
        const data = await this.makeRequest('/reset_deadline', {
            method: 'POST'
        });
        
        if (data && data.success) {
            this.state.deadline = null;
            this.state.deadlineDisplay = null;
            
            // CRITICAL FIX: Update the global window variable
            window.deadlineSet = false;
            
            // Update UI
            if (this.elements.deadlineDisplay) {
                this.elements.deadlineDisplay.style.display = 'none';
            }
            if (this.elements.countdown) {
                this.elements.countdown.textContent = '--:--:--';
                this.elements.countdown.className = 'countdown';
            }
            if (this.elements.spentTime) {
                this.elements.spentTime.textContent = '0:00';
            }
            
            this.showSuccess('Timer reset successfully!');
        }
    }
    
    async clearTasks() {
        const data = await this.makeRequest('/clear_tasks', {
            method: 'POST'
        });
        
        if (data && data.success) {
            this.state.tasks = [];
            this.updateTaskDisplay();
            this.updateCurrentTaskDisplay();
            this.showSuccess('All tasks cleared!');
        }
    }
    
    async updatePriority(selectElement) {
        const form = selectElement.closest('form');
        if (!form) return;
        
        const formData = new FormData(form);
        const taskId = this.getTaskIdFromRow(selectElement.closest('tr'));
        
        const data = await this.makeRequest(`/update_priority/${taskId}`, {
            method: 'POST',
            body: formData
        });
        
        if (data && data.success) {
            // Update local state
            if (this.state.tasks[taskId]) {
                this.state.tasks[taskId].priority = data.priority;
            }
            
            // Update visual styling
            this.updatePrioritySelectBorder(selectElement);
            this.showSuccess('Priority updated!');
        }
    }
    
    async updateTaskDeadline(selectElement) {
        const form = selectElement.closest('form');
        if (!form) return;
        
        const formData = new FormData(form);
        const taskId = this.getTaskIdFromRow(selectElement.closest('tr'));
        
        const data = await this.makeRequest(`/update_task_deadline/${taskId}`, {
            method: 'POST',
            body: formData
        });
        
        if (data && data.success) {
            // Update local state
            if (this.state.tasks[taskId]) {
                this.state.tasks[taskId].task_deadline = data.deadline;
            }
            
            // Update countdown display
            const row = selectElement.closest('tr');
            const deadlineCell = row.querySelector('.deadline-cell');
            
            if (data.deadline) {
                let countdownDiv = deadlineCell.querySelector('.task-countdown');
                if (!countdownDiv) {
                    countdownDiv = document.createElement('div');
                    countdownDiv.className = 'task-countdown';
                    deadlineCell.appendChild(countdownDiv);
                }
                countdownDiv.setAttribute('data-deadline', data.deadline);
            } else {
                const countdownDiv = deadlineCell.querySelector('.task-countdown');
                if (countdownDiv) {
                    countdownDiv.remove();
                }
            }
            
            this.showSuccess('Deadline updated!');
        }
    }
    
    async addTaskFrom(link) {
        const url = link.href;
        const data = await this.makeRequest(url);
        
        if (data && data.success) {
            this.state.tasks.push(data.task);
            this.addTaskToTable(data.task, data.task_index);
            this.updateCurrentTaskDisplay();
            this.showSuccess('Task added from history!');
        }
    }
    
    async sortTasks(button) {
        const form = button.closest('form');
        const url = form ? form.action : button.getAttribute('data-sort-url');
        
        const data = await this.makeRequest(url, {
            method: 'POST'
        });
        
        if (data && data.success) {
            this.state.tasks = data.tasks;
            this.updateTaskDisplay();
            this.showSuccess(`Tasks sorted by ${data.sort_type.replace('_', ' ')}!`);
        }
    }
    
    getTaskIdFromRow(row) {
        // Get task ID from row position
        return Array.from(row.parentNode.children).indexOf(row);
    }
    
    refreshFavoritesTable() {
        // Optionally implement favorites table refresh
        // For now, we'll rely on the state being updated
    }
    
    initializePrioritySelects() {
        const prioritySelects = document.querySelectorAll('.priority-select');
        prioritySelects.forEach(select => {
            this.updatePrioritySelectBorder(select);
        });
    }
    
    updatePrioritySelectBorder(select) {
        const selectedOption = select.options[select.selectedIndex];
        if (selectedOption) {
            const priorityValue = parseInt(selectedOption.value);
            let borderColor = this.getPriorityColor(priorityValue);
            
            select.style.borderColor = borderColor;
            select.style.borderWidth = '2px';
        }
    }
    
    getPriorityColor(priorityValue) {
        // Lower numbers = higher priority = redder colors
        switch(priorityValue) {
            case 1: return '#dc3545'; // Red - highest priority
            case 2: return '#fd7e14'; // Orange
            case 3: return '#ffc107'; // Yellow
            case 4: return '#20c997'; // Teal
            case 5: return '#28a745'; // Green - lowest priority
            default: return '#6c757d'; // Gray
        }
    }
    
    // ====== TIMER FUNCTIONS ======
    updateMainTimers() {
        // 1) Main countdown
        if (!window.deadlineSet) {
            if (this.elements.countdown) {
                this.elements.countdown.innerText = "--:--:--";
            }
            if (this.elements.spentTime) {
                this.elements.spentTime.innerText = "0:00";
            }
            return;
        }
    
        fetch('/get_remaining_time')
            .then(r => r.text())
            .then(secondsStr => {
                let sec = parseInt(secondsStr);
                if (sec <= 0) {
                    this.elements.countdown.innerText = "Time's up!";
                    this.elements.countdown.classList.remove('low-time');
                    this.elements.countdown.classList.add('all-done');
                } else {
                    // Calculate hours, minutes, seconds
                    let hrs = Math.floor(sec / 3600);
                    sec %= 3600;
                    let mins = Math.floor(sec / 60);
                    let secs = sec % 60;
    
                    // Toggle the red color when <= 900 seconds (15 minutes)
                    if (sec + mins * 60 + hrs * 3600 <= 900) {
                        this.elements.countdown.classList.add('low-time');
                        this.elements.countdown.classList.remove('all-done');
                    } else {
                        this.elements.countdown.classList.remove('low-time');
                        this.elements.countdown.classList.remove('all-done');
                    }
    
                    // Format the display
                    if (hrs < 1) {
                        const secsPadded = secs.toString().padStart(2, '0');
                        this.elements.countdown.innerText = mins + ":" + secsPadded;
                    } else {
                        this.elements.countdown.innerText = hrs + ":" + mins + ":" + secs;
                    }
                }
            })
            .catch(err => {
                console.warn('Error fetching remaining time:', err);
                if (this.elements.countdown) {
                    this.elements.countdown.innerText = "--:--:--";
                }
            });
    
        // 2) Spent time (time since last completion or countdown start)
        fetch('/get_spent_time')
            .then(r => r.text())
            .then(spentStr => {
                let spent = parseInt(spentStr);
                if (spent < 0) {
                    this.elements.spentTime.innerText = "0:00";
                    return;
                }
                let hrs = Math.floor(spent / 3600);
                let remainder = spent % 3600;
                let mins = Math.floor(remainder / 60);
                let secs = remainder % 60;
    
                // If under an hour => M:SS
                if (hrs < 1) {
                    this.elements.spentTime.innerText = mins + ":" + secs.toString().padStart(2, '0');
                } else {
                    const minsStr = mins.toString().padStart(2, '0');
                    const secsStr = secs.toString().padStart(2, '0');
                    this.elements.spentTime.innerText = hrs + ":" + minsStr + ":" + secsStr;
                }
            })
            .catch(err => {
                console.warn('Error fetching spent time:', err);
                if (this.elements.spentTime) {
                    this.elements.spentTime.innerText = "0:00";
                }
            });
    }
    
    updateTaskDeadlineCountdowns() {
        const taskCountdowns = document.querySelectorAll('.task-countdown');
        const now = new Date();
        
        taskCountdowns.forEach(countdown => {
            // Skip if this task is completed
            const taskRow = countdown.closest('tr');
            const taskCell = taskRow.querySelector('.task-cell');
            if (taskCell.classList.contains('task-completed')) {
                countdown.innerText = "Completed";
                countdown.style.color = '#fff';
                countdown.style.backgroundColor = 'transparent';
                countdown.style.borderColor = 'transparent';
                return;
            }
            
            const deadlineStr = countdown.getAttribute('data-deadline');
            if (!deadlineStr) return;
            
            const deadline = new Date(deadlineStr);
            const timeDiff = deadline - now;
            
            if (timeDiff <= 0) {
                countdown.innerText = "OVERDUE";
                countdown.classList.add('overdue-text');
            } else {
                countdown.classList.remove('overdue-text');
                
                const hours = Math.floor(timeDiff / (1000 * 60 * 60));
                const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
                
                if (hours > 0) {
                    countdown.innerText = `${hours}h ${minutes}m`;
                } else if (minutes > 0) {
                    countdown.innerText = `${minutes}m ${seconds}s`;
                } else {
                    countdown.innerText = `${seconds}s`;
                }
                
                // Add warning style when less than 15 minutes remaining
                if (timeDiff <= 15 * 60 * 1000) {
                    countdown.style.color = '#dc3545';
                    countdown.style.backgroundColor = '#fff3cd';
                    countdown.style.borderColor = '#ffc107';
                } else {
                    countdown.style.color = '#007BFF';
                    countdown.style.backgroundColor = '#f8f9fa';
                    countdown.style.borderColor = '#dee2e6';
                }
            }
        });
    }
    
    // ====== FOCUS MODE SUPPORT ======
    initFocusMode() {
        // Placeholder for focus mode initialization
        // The existing focus mode code can be integrated here
        console.log('Focus mode initialized');
    }
    
    launchConfetti() {
        if (typeof confetti !== 'undefined') {
            const duration = 3000;
            const end = Date.now() + duration;

            (function frame() {
                confetti({
                    particleCount: 5,
                    startVelocity: 30,
                    spread: 360,
                    ticks: 60,
                    origin: {
                        x: Math.random(),
                        y: Math.random() - 0.2
                    }
                });
                if (Date.now() < end) {
                    requestAnimationFrame(frame);
                }
            }());
        }
    }

    // ====== EXISTING FUNCTIONALITY (UPDATED) ======
    startTimers() {
        if (window.allDone) {
            if (this.elements.countdown) {
                this.elements.countdown.innerText = "All tasks complete";
                this.elements.countdown.style.color = "green";
            }
            if (this.elements.spentTime) {
                this.elements.spentTime.innerText = "0:00";
            }
            this.launchConfetti();
            return;
        }
        
        this.timers.main = setInterval(() => this.updateMainTimers(), 1000);
        this.timers.deadlines = setInterval(() => this.updateTaskDeadlineCountdowns(), 1000);
        this.updateMainTimers();
    }
    
    // ... (include existing timer functions with minimal modifications)
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.taskTracker = new TaskTrackerApp();
});

// Legacy functions for backwards compatibility
function launchConfetti() {
    // ... existing confetti function
}

/**
 * Utility function to show notifications (for future enhancements)
 */
function showNotification(message, type = 'info') {
    // This can be enhanced with a proper notification system
    console.log(`${type.toUpperCase()}: ${message}`);
}

/**
 * Add keyboard shortcuts for power users
 */
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to quickly add task
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const taskInput = document.querySelector('input[name="task_text"]');
        if (taskInput && !taskInput.value.trim()) {
            taskInput.focus();
            e.preventDefault();
        }
    }
    
    // Escape to clear focused input
    if (e.key === 'Escape') {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.tagName === 'INPUT') {
            activeElement.blur();
        }
    }
});
