
function togglePassword(inputId, button) {
    const passwordInput = document.getElementById(inputId);

    if (!passwordInput) {
        return;
    }

    const isHidden = passwordInput.type === "password";

    passwordInput.type = isHidden ? "text" : "password";
    button.textContent = isHidden ? "Hide" : "Show";

    button.setAttribute(
        "aria-label",
        isHidden ? "Hide password" : "Show password"
    );
}
