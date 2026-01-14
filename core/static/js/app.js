document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("sidebarToggle");
    if (toggle) {
        toggle.addEventListener("click", () => {
            document.body.classList.toggle("sidebar-open");
        });
    }
});
