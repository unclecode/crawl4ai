(() => {
    // Function to extract image data from Google Images page
    function extractImageData() {
        const keys = Object.keys(window.W_jd);
        let allImageData = [];
        let currentPosition = 0;

        // Get the symbol we'll use (from first valid entry)
        let targetSymbol;
        for (let key of keys) {
            try {
                const symbols = Object.getOwnPropertySymbols(window.W_jd[key]);
                if (symbols.length > 0) {
                    targetSymbol = symbols[0];
                    break;
                }
            } catch (e) {
                continue;
            }
        }

        if (!targetSymbol) return [];

        // Iterate through ALL keys
        for (let key of keys) {
            try {
                const o1 = window.W_jd[key][targetSymbol]
                if (!o1) continue;
                const data = Object.values(o1)[0]
                // const data = window.W_jd[key][targetSymbol]?.Ws;
                // Check if this is a valid image data entry
                if (data && Array.isArray(data[1])) {
                    const processedData = processImageEntry(data, currentPosition);
                    if (processedData) {
                        allImageData.push(processedData);
                        currentPosition++;
                    }
                }
            } catch (e) {
                continue;
            }
        }

        return allImageData;
    }

    function processImageEntry(entry, position) {
        const imageData = entry[1];
        if (!Array.isArray(imageData)) return null;

        // Extract the image ID
        const imageId = imageData[1];
        if (!imageId) return null;

        // Find the corresponding DOM element
        const domElement = document.querySelector(`[data-docid="${imageId}"]`);
        if (!domElement) return null;

        // Extract data from the array structure
        const [
            _,
            id,
            thumbnailInfo,
            imageInfo,
            __,
            ___,
            rgb,
            ____,
            _____,
            metadata
        ] = imageData;

        // Ensure we have the required data
        if (!thumbnailInfo || !imageInfo) return null;

        // Extract metadata from DOM
        const title = domElement?.querySelector('.toI8Rb')?.textContent?.trim();
        const source = domElement?.querySelector('.guK3rf')?.textContent?.trim();
        const link = domElement?.querySelector('a.EZAeBe')?.href;

        if (!link) return null;

        // Build Google Image URL
        const googleUrl = buildGoogleImageUrl(imageInfo[0], link, imageId, imageInfo[1], imageInfo[2]);

        return {
            title,
            imageUrl: imageInfo[0],
            imageWidth: imageInfo[2],
            imageHeight: imageInfo[1],
            thumbnailUrl: thumbnailInfo[0],
            thumbnailWidth: thumbnailInfo[2],
            thumbnailHeight: thumbnailInfo[1],
            source,
            domain: metadata['2000']?.[1] || new URL(link).hostname,
            link,
            googleUrl,
            position: position + 1
        };
    }

    function buildGoogleImageUrl(imgUrl, refUrl, tbnid, height, width) {
        const params = new URLSearchParams({
            imgurl: imgUrl,
            tbnid: tbnid,
            imgrefurl: refUrl,
            docid: tbnid,
            w: width.toString(),
            h: height.toString(),
        });

        return `https://www.google.com/imgres?${params.toString()}`;
    }
    return extractImageData();
})();