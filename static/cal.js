const monthYearElement = document.getElementById('monthYear');
const datesElement = document.getElementById('dates');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');

let currentDate = new Date();

const updateCalendar = () => {
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth();

    const firstDay = new Date(currentYear, currentMonth, 1); // First day of the month
    const lastDay = new Date(currentYear, currentMonth + 1, 0); // Last day of the month

    const totalDays = lastDay.getDate(); // Total days in the current month
    const firstDayIndex = firstDay.getDay(); // Index of the first day (0 = Sunday, 1 = Monday, ...)
    const lastDayIndex = lastDay.getDay(); // Index of the last day (0 = Sunday, 1 = Monday, ...)

    const monthYearString = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });
    monthYearElement.textContent = monthYearString;

    let datesHTML = '';

    // Add previous month's days to fill in the empty space before the first day
    for (let i = firstDayIndex; i > 0; i--) {
        const prevDate = new Date(currentYear, currentMonth, 1 - i); // Days from the previous month
        datesHTML += `<div class="date inactive">${prevDate.getDate()}</div>`;
    }

    // Add current month's days
    for (let i = 1; i <= totalDays; i++) {
        const date = new Date(currentYear, currentMonth, i);
        const activeClass = date.toDateString() === new Date().toDateString() ? 'active' : '';
        datesHTML += `<div class="date ${activeClass}">${i}</div>`;
    }

    // Add next month's days to fill the empty space after the last day
    for (let i = 1; i <= (6 - lastDayIndex); i++) {
        const nextDate = new Date(currentYear, currentMonth + 1, i); // Days from the next month
        datesHTML += `<div class="date inactive">${nextDate.getDate()}</div>`;
    }

    datesElement.innerHTML = datesHTML;
};

// Event listeners for navigation buttons
prevBtn.addEventListener('click', () => {
    event.preventDefault();
    currentDate.setMonth(currentDate.getMonth() - 1); // Move to the previous month
    updateCalendar();
});

nextBtn.addEventListener('click', () => {
    event.preventDefault();
    currentDate.setMonth(currentDate.getMonth() + 1); // Move to the next month
    updateCalendar();
});

updateCalendar();
