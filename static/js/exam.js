const examRoot = document.querySelector("[data-exam-root]");

if (examRoot) {
    const cards = Array.from(document.querySelectorAll("[data-question-card]"));
    const paletteButtons = Array.from(document.querySelectorAll("[data-jump]"));
    const prevButton = document.getElementById("prev-question");
    const nextButton = document.getElementById("next-question");
    const form = document.getElementById("exam-form");
    const countdown = document.getElementById("countdown");
    const submitButton = document.getElementById("submit-exam-button");
    let currentIndex = 0;
    let remaining = Number(examRoot.dataset.remaining || 0);

    const updatePaletteState = () => {
        paletteButtons.forEach((button, index) => {
            const card = cards[index];
            const hasAnswer = card.querySelector("input:checked");
            button.classList.toggle("active", index === currentIndex);
            button.classList.toggle("answered", Boolean(hasAnswer));
        });
    };

    const showCard = (index) => {
        currentIndex = Math.max(0, Math.min(index, cards.length - 1));
        cards.forEach((card, cardIndex) => {
            card.classList.toggle("active", cardIndex === currentIndex);
        });
        updatePaletteState();
    };

    const renderTime = () => {
        const safeRemaining = Math.max(remaining, 0);
        const minutes = String(Math.floor(safeRemaining / 60)).padStart(2, "0");
        const seconds = String(safeRemaining % 60).padStart(2, "0");
        countdown.textContent = `${minutes}:${seconds}`;
    };

    const totalAnswered = () => form.querySelectorAll("input[type='radio']:checked").length;

    paletteButtons.forEach((button) => {
        button.addEventListener("click", () => showCard(Number(button.dataset.jump)));
    });

    form.addEventListener("change", updatePaletteState);
    prevButton.addEventListener("click", () => showCard(currentIndex - 1));
    nextButton.addEventListener("click", () => showCard(currentIndex + 1));

    submitButton.addEventListener("click", (event) => {
        const answered = totalAnswered();
        const total = cards.length;
        const confirmed = window.confirm(
            `You have answered ${answered} of ${total} questions. Unanswered questions will be marked as Not Attempted. Are you sure?`
        );
        if (!confirmed) {
            event.preventDefault();
        }
    });

    renderTime();
    updatePaletteState();

    const timer = window.setInterval(() => {
        remaining -= 1;
        renderTime();
        if (remaining <= 0) {
            window.clearInterval(timer);
            form.submit();
        }
    }, 1000);
}
