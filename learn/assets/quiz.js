/* Shared quiz component — retrieval practice with immediate feedback.
 *
 * Markup contract:
 *   <div class="quiz" data-answer="1">
 *     <p class="q">Question?</p>
 *     <button>Option A</button>
 *     <button>Option B</button>
 *     <div class="feedback" data-correct="..." data-wrong="..."></div>
 *   </div>
 *
 * data-answer is the zero-based index of the correct button.
 *
 * Two deliberate choices, both about not leaking the answer:
 *   - Options are NOT shuffled. They are authored equal-length on purpose, and
 *     shuffling would make the authored parallelism harder to audit.
 *   - Every option stays visible after answering. Hiding the wrong ones robs
 *     the learner of the contrast that makes the correction stick.
 */
(function () {
  function wire(quiz) {
    const answer = Number(quiz.dataset.answer);
    const buttons = Array.from(quiz.querySelectorAll("button"));
    const feedback = quiz.querySelector(".feedback");

    buttons.forEach((button, index) => {
      button.addEventListener("click", () => {
        if (quiz.dataset.done === "true") return;
        quiz.dataset.done = "true";

        buttons.forEach((b) => {
          b.disabled = true;
        });
        buttons[answer].classList.add("correct");
        if (index !== answer) button.classList.add("wrong");

        if (feedback) {
          const right = index === answer;
          feedback.textContent = (right ? "Correct. " : "Not quite. ") +
            (right ? (feedback.dataset.correct || "") : (feedback.dataset.wrong || ""));
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".quiz").forEach(wire);
  });
})();
