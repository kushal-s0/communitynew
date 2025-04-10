document.addEventListener("DOMContentLoaded", function () {
    const gallery = document.querySelector(".gallery");
    const originalImages = Array.from(gallery.children);
    const imageWidth = originalImages[0].offsetWidth + 40; // includes margin/padding
    let index = 0;

    // Clone all original images twice for infinite effect
    for (let i = 0; i < 2; i++) {
        originalImages.forEach((img) => {
            gallery.appendChild(img.cloneNode(true));
        });
    }

    function updateActiveImage() {
        const allImages = document.querySelectorAll(".gallery .image-container img");
        allImages.forEach(img => img.classList.remove("active"));

        const activeContainer = document.querySelectorAll(".gallery .image-container")[index + 1];
        if (activeContainer) {
            const img = activeContainer.querySelector("img");
            if (img) img.classList.add("active");
        }
    }

    function slideCarousel() {
        index++;
        gallery.style.transition = "transform 1s ease-in-out";
        gallery.style.transform = `translateX(-${index * imageWidth}px)`;
        updateActiveImage();

        if (index >= originalImages.length*2) {
            setTimeout(() => {
                gallery.style.transition = "none";
                gallery.style.transform = `translateX(0)`;
                index = 0;
                updateActiveImage();
            }, 1000);
        }
    }

    let autoSlide = setInterval(slideCarousel, 3000);

    function resetAutoSlide() {
        clearInterval(autoSlide);
        autoSlide = setInterval(slideCarousel, 3000);
    }

    window.prevSlide = function () {
        if (index === 0) {
            index = originalImages.length;
            gallery.style.transition = "none";
            gallery.style.transform = `translateX(-${index * imageWidth}px)`;
        }

        setTimeout(() => {
            index--;
            gallery.style.transition = "transform 1s ease-in-out";
            gallery.style.transform = `translateX(-${index * imageWidth}px)`;
            updateActiveImage();
        }, 20);

        clearInterval(autoSlide);
        setTimeout(resetAutoSlide, 1000);
    };

    window.nextSlide = function () {
        slideCarousel();
        clearInterval(autoSlide);
        setTimeout(resetAutoSlide, 1000);
    };

    updateActiveImage();
});

document.addEventListener("DOMContentLoaded", function () {
    const userIcon = document.querySelector(".user-icon");
    const sidebar = document.querySelector(".dropdown-menu");
    const body = document.body;

    userIcon.addEventListener("click", function (event) {
        event.stopPropagation(); // Prevents closing when clicking the icon
        sidebar.classList.toggle("show"); // Show/hide sidebar
        body.classList.toggle("sidebar-active"); // Add blur effect
    });

    document.addEventListener("click", function (event) {
        if (!sidebar.contains(event.target) && !userIcon.contains(event.target)) {
            sidebar.classList.remove("show");
            body.classList.remove("sidebar-active");
        }
    });
});

  function setupAutoScroll(containerId) {
    const container = document.getElementById(containerId);
    const items = container.children;
    const total = items.length;
    let index = 0;
    const delay = 3000;

    if (total <= 5) return;

    const itemHeight = items[0].offsetHeight ;

    function scrollNext() {
      if (index < total - 3) {
        index++;
      } else {
        index = 0;
        container.style.transition = "none";
        container.style.transform = `translateY(0px)`;
        setTimeout(() => {
          container.style.transition = "transform 0.5s ease-in-out";
          scrollNext();
        }, delay);
        return;
      }
      container.style.transform = `translateY(-${itemHeight * index}px)`;
      setTimeout(scrollNext, delay);
    }

    setTimeout(scrollNext, delay);
  }

  document.addEventListener("DOMContentLoaded", function () {
    setupAutoScroll("announcements-scroll");
    setupAutoScroll("events-scroll");
  });
