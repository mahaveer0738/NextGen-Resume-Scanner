// Smooth scroll for nav links and buttons
function scrollToUpload() {
    const heroSection = document.getElementById('hero');
    if (heroSection) {
        heroSection.scrollIntoView({ behavior: 'smooth' });
    }
}

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Drag and drop functionality
const dropzone = document.getElementById('uploadDropzone');
const fileInput = document.getElementById('resumeInput');

if (dropzone) {
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--secondary)';
        dropzone.style.backgroundColor = 'var(--bg-alt)';
    });

    dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--primary)';
        dropzone.style.backgroundColor = 'var(--bg-card)';
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--primary)';
        dropzone.style.backgroundColor = 'var(--bg-card)';
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload(fileInput);
        }
    });
}

function handleFileUpload(input) {
    const file = input.files[0];
    if (file) {
        // Validate file type
        const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|doc|docx)$/i)) {
            alert('Please upload a PDF or DOCX file.');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('File is too large. Max size is 5MB.');
            return;
        }

        document.getElementById('dropzoneContent').style.display = 'none';
        document.getElementById('fileSelectedState').style.display = 'block';
        document.getElementById('uploadedFileName').textContent = file.name;
    }
}

function resetUpload() {
    document.getElementById('resumeInput').value = '';
    document.getElementById('dropzoneContent').style.display = 'block';
    document.getElementById('fileSelectedState').style.display = 'none';
}

function analyzeResume() {
    const analyzeBtn = document.querySelector('.analyze-btn');
    
    // Simulate loading state
    analyzeBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
    analyzeBtn.disabled = true;

    // In a real app, this would upload the file and wait for a response.
    // For this demo, we'll redirect to the results page after a delay.
    setTimeout(() => {
        window.location.href = 'pages/results.html';
    }, 1500);
}
