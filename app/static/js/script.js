
/* =========================================
   CIVISPHERE - GLOBAL JAVASCRIPT
========================================= */

document.addEventListener("DOMContentLoaded", function () {

    // 1. Mobile navigation menu
    const menuToggle = document.querySelector("[data-menu-toggle]");
    const navigationMenu = document.querySelector("[data-navigation-menu]");

    if (menuToggle && navigationMenu) {
        menuToggle.addEventListener("click", function () {
            navigationMenu.classList.toggle("active");

            const expanded =
                menuToggle.getAttribute("aria-expanded") === "true";

            menuToggle.setAttribute("aria-expanded", String(!expanded));
        });
    }

    // 2. Password visibility toggle
    document.querySelectorAll("[data-toggle-password]").forEach(function (button) {
        button.addEventListener("click", function () {
            const inputId = button.dataset.togglePassword;
            const passwordInput = document.getElementById(inputId);

            if (!passwordInput) return;

            const isPassword = passwordInput.type === "password";
            passwordInput.type = isPassword ? "text" : "password";

            button.textContent = isPassword ? "Hide" : "Show";
            button.setAttribute(
                "aria-label",
                isPassword ? "Hide password" : "Show password"
            );
        });
    });

    // 3. Confirm important actions
    document.querySelectorAll("[data-confirm]").forEach(function (element) {
        element.addEventListener("click", function (event) {
            const message = element.dataset.confirm || "Are you sure?";

            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // 4. Automatically dismiss flash messages
    document.querySelectorAll("[data-auto-dismiss]").forEach(function (message) {
        const delay = Number(message.dataset.autoDismiss) || 5000;

        window.setTimeout(function () {
            message.classList.add("fade-out");

            window.setTimeout(function () {
                message.remove();
            }, 400);
        }, delay);
    });

    // 5. Close mobile menu after selecting a link
    if (navigationMenu) {
        navigationMenu.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                navigationMenu.classList.remove("active");

                if (menuToggle) {
                    menuToggle.setAttribute("aria-expanded", "false");
                }
            });
        });
    }

    // 6. Update current year
    document.querySelectorAll("[data-current-year]").forEach(function (element) {
        element.textContent = new Date().getFullYear();
    });

    // 7. Back to top button
    const backToTop = document.querySelector("[data-back-to-top]");

    if (backToTop) {
        backToTop.addEventListener("click", function () {
            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
        });
    }

});
