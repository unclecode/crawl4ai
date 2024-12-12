() => {
    return new Promise((resolve) => {
        const filterImage = (img) => {
            // Filter out images that are too small
            if (img.width < 100 && img.height < 100) return false;

            // Filter out images that are not visible
            const rect = img.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return false;

            // Filter out images with certain class names (e.g., icons, thumbnails)
            if (img.classList.contains("icon") || img.classList.contains("thumbnail")) return false;

            // Filter out images with certain patterns in their src (e.g., placeholder images)
            if (img.src.includes("placeholder") || img.src.includes("icon")) return false;

            return true;
        };

        const images = Array.from(document.querySelectorAll("img")).filter(filterImage);
        let imagesLeft = images.length;

        if (imagesLeft === 0) {
            resolve();
            return;
        }

        const checkImage = (img) => {
            if (img.complete && img.naturalWidth !== 0) {
                img.setAttribute("width", img.naturalWidth);
                img.setAttribute("height", img.naturalHeight);
                imagesLeft--;
                if (imagesLeft === 0) resolve();
            }
        };

        images.forEach((img) => {
            checkImage(img);
            if (!img.complete) {
                img.onload = () => {
                    checkImage(img);
                };
                img.onerror = () => {
                    imagesLeft--;
                    if (imagesLeft === 0) resolve();
                };
            }
        });

        // Fallback timeout of 5 seconds
        // setTimeout(() => resolve(), 5000);
        resolve();
    });
};
