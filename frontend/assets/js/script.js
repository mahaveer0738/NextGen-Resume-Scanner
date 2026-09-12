/* =========================
   MOBILE MENU
========================= */

const menuBtn = document.getElementById("menuBtn");
const navLinks = document.getElementById("navLinks");

menuBtn.addEventListener("click", () => {

    navLinks.classList.toggle("active");

    const icon = menuBtn.querySelector("i");

    if (navLinks.classList.contains("active")) {
        icon.classList.remove("fa-bars");
        icon.classList.add("fa-xmark");
    } else {
        icon.classList.remove("fa-xmark");
        icon.classList.add("fa-bars");
    }

});


/* Close mobile menu after clicking link */

document.querySelectorAll(".nav-links a").forEach(link => {

    link.addEventListener("click", () => {

        navLinks.classList.remove("active");

        const icon = menuBtn.querySelector("i");

        icon.classList.remove("fa-xmark");
        icon.classList.add("fa-bars");

    });

});


/* =========================
   SCROLL FUNCTIONS
========================= */

function scrollToAnalyzer() {

    document.getElementById("analyzer").scrollIntoView({
        behavior: "smooth"
    });

}


function scrollToTemplates() {

    document.getElementById("templates").scrollIntoView({
        behavior: "smooth"
    });

}


/* =========================
   RESUME FILE UPLOAD
========================= */

const resumeInput = document.getElementById("resumeInput");
const uploadCard = document.getElementById("uploadCard");
const fileName = document.getElementById("fileName");


resumeInput.addEventListener("change", function () {

    if (this.files.length === 0) {
        return;
    }

    const file = this.files[0];

    validateFile(file);

});


function validateFile(file) {

    const maxSize = 5 * 1024 * 1024;

    const allowedTypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ];

    if (!allowedTypes.includes(file.type)) {

        fileName.innerHTML =
            "❌ Please upload PDF, DOC or DOCX file.";

        return;
    }


    if (file.size > maxSize) {

        fileName.innerHTML =
            "❌ File size must be less than 5MB.";

        return;
    }


    fileName.innerHTML =
        `✓ ${file.name} selected successfully`;

}


/* =========================
   DRAG & DROP
========================= */

uploadCard.addEventListener("dragover", function (event) {

    event.preventDefault();

    uploadCard.classList.add("dragover");

});


uploadCard.addEventListener("dragleave", function () {

    uploadCard.classList.remove("dragover");

});


uploadCard.addEventListener("drop", function (event) {

    event.preventDefault();

    uploadCard.classList.remove("dragover");

    const files = event.dataTransfer.files;

    if (files.length > 0) {

        const file = files[0];

        resumeInput.files = files;

        validateFile(file);

    }

});


/* =========================
   TOOL BUTTON DEMO
========================= */

const toolButtons =
    document.querySelectorAll(".tool-card button");


toolButtons.forEach(button => {

    button.addEventListener("click", function () {

        const toolName =
            this.parentElement.querySelector("h3").textContent;

        if (toolName === "ATS Resume Checker") {

            scrollToAnalyzer();

        } else {

            alert(
                `${toolName} will be available soon!`
            );

        }

    });

});


/* =========================
   TEMPLATE BUTTONS
========================= */

const templateButtons =
    document.querySelectorAll(".template-info button");


templateButtons.forEach(button => {

    button.addEventListener("click", function () {

        alert(
            "Template selected! Resume Builder will open here."
        );

    });

});


/* =========================
   LOGIN BUTTON
========================= */

const loginBtn =
    document.querySelector(".login-btn");


loginBtn.addEventListener("click", () => {

    alert("Login page will open here.");

});


/* =========================
   SIMPLE SCROLL ANIMATION
========================= */

const observer =
    new IntersectionObserver(
        entries => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {

                    entry.target.style.opacity = "1";
                    entry.target.style.transform = "translateY(0)";

                }

            });

        },
        {
            threshold: 0.1
        }
    );


document
    .querySelectorAll(
        ".tool-card, .template-card, .step, .upload-feature"
    )
    .forEach(element => {

        element.style.opacity = "0";

        element.style.transform = "translateY(25px)";

        element.style.transition =
            "opacity 0.6s ease, transform 0.6s ease";

        observer.observe(element);

    });