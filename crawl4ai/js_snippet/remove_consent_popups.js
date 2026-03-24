async () => {
    // Helper: check if element is visible
    const isVisible = (elem) => {
        if (!elem) return false;
        const style = window.getComputedStyle(elem);
        return style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0";
    };

    // =========================================================================
    // Phase 1: Click "Accept All" buttons (fastest, cleanest dismissal)
    // =========================================================================

    // CMP-specific accept button selectors (ordered by market share)
    const cmpAcceptSelectors = [
        // OneTrust / CookiePro
        '#onetrust-accept-btn-handler',
        '#accept-recommended-btn-handler',
        // Cookiebot (Usercentrics/Cybot)
        '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
        '#CybotCookiebotDialogBodyButtonAccept',
        '#CybotCookiebotDialogBodyLevelButtonAccept',
        // Didomi
        '#didomi-notice-agree-button',
        '.didomi-button-highlight',
        // Quantcast Choice
        '.qc-cmp2-summary-buttons button[mode="primary"]',
        // Sourcepoint
        '.sp_choice_type_11',
        '.sp_choice_type_ACCEPT_ALL',
        // Google FundingChoices / FC
        '.fc-button.fc-cta-consent.fc-primary-button',
        '.fc-cta-consent',
        '.fc-confirm-choices',
        // TrustArc
        '#truste-consent-button',
        '.truste_popframe .pdynamicbutton .call',
        // ConsentManager.net
        '.cmpboxbtnyes',
        '#cmpwelcomebtnyes',
        '.cmpboxbtnyescustomchoices',
        // Osano
        '.osano-cm-accept-all',
        '.osano-cm-accept',
        // Iubenda
        '#iubenda-cs-accept-btn',
        '.iubenda-cs-accept-btn',
        // Complianz (WordPress)
        '.cmplz-btn.cmplz-accept',
        // LiveRamp / Fides (Ethyca)
        '.fides-accept-all-button',
        '#fides-banner .fides-accept-all-button',
        // CookieYes
        '.cky-btn-accept',
        '[data-cky-tag="accept-button"]',
        // Klaro
        '.klaro .cm-btn-accept-all',
        '.klaro .cm-btn-success',
        '.klaro .cookie-notice .cm-btn-success',
        // Termly
        '[data-tid="banner-accept"]',
        // CookieFirst
        'button[data-cookiefirst-action="accept"]',
        // CookieScript
        '#cookiescript_accept',
        // Borlabs Cookie (WordPress)
        'a[data-cookie-accept-all]',
        '.brlbs-btn-accept-all',
        // Civic Cookie Control
        '#ccc-recommended-settings',
        '#ccc-notify-accept',
        '.ccc-accept-button',
        // Cookie Information
        '.coi-banner__accept',
        // Evidon / Crownpeak
        '#_evidon-accept-button',
        // Axeptio
        'button#axeptio_btn_acceptAll',
        // HubSpot
        '#hs-eu-confirmation-button',
        // Ketch
        '#lanyard_root button[class*="confirmButton"]',
        // Moove GDPR (WordPress)
        '.moove-gdpr-infobar-allow-all',
        // TermsFeed
        '.cc-nb-okagree',
        // tarteaucitron.js
        '#tarteaucitronPersonalize2',
        '.tarteaucitronAllow',
        // CookieHub
        '.ch2-allow-all-btn',
        // Cookie Notice (WP plugin)
        '#cn-accept-cookie',
        // EU Cookie Compliance (Drupal)
        '.eu-cookie-compliance-banner .agree-button',
        '.eu-cookie-compliance-banner .accept-all',
        // WordPress GDPR Cookie Consent
        '#gdpr-cookie-consent-bar #cookie_action_accept',
        // Cookie Law Info / WebToffee
        '[data-cli_action="accept"]',
        // Shopify Native
        '#shopify-pc__banner__btn-accept',
        // Wix Native
        '[data-hook="ccsu-banner-accept"]',
        // Finsweet (Webflow)
        '[fs-consent-element="allow"]',
        '[fs-cc="banner"] [fs-cc="allow"]',
        // Pandectes (Shopify)
        '#pandectes-banner .cc-allow',
        // Clickio
        '#cl-consent [data-role="b_agree"]',
        // Snigel
        '.snigel-cmp-framework #accept-choices',
        // Cassie
        '.cassie-accept-all',
        // FastCMP
        '.fast-cmp-home-accept button',
        // Sibbo
        '#acceptAllMain',
        // PubTech
        '#pt-accept-all',
        // UniConsent
        '#unic-agree',
        // Ezoic
        '#ez-accept-all',
        // Transcend
        '#transcend-consent-manager .inner-container button',
        // Cloudflare Zaraz
        '#cf_consent-buttons__accept-all',
        // CookieConsent v2 (Insites/Osano OSS)
        '#s-all-bn',
        // CookieConsent v3 (orestbida)
        '.cm__btn[data-role="all"]',
        // Openli / Legal Monster
        '#lm-accept-all',
        // UK Cookie Consent (Catapult)
        '#catapultCookie',
        // Mediavine
        '[data-name="mediavine-gdpr-cmp"] [format="primary"]',
        // Consentmo (Shopify)
        '.isense-cc-allow',
        // AdOpt
        '#adopt-accept-all-button',
        // Truyo
        'button#acceptAllCookieButton',
        // KConsent
        '#kc-acceptAndHide',
        // Gravito
        '#modalConfirmBtn.gravitoCMP-button',
        // CT Ultimate GDPR (WordPress)
        '#ct-ultimate-gdpr-cookie-accept',
        // Hu-manity
        '[data-hu-action="cookies-notice-consent-choices-3"]',
        // GDPR Legal Cookie (Shopify)
        '.overlay_bc_banner *[data-cookie-accept-all]',
        // Bing / Microsoft
        '#bnp_btn_accept',
        // Privado
        '#cookie-consent-banner #accept-button',
        // Cookie Alert
        'button[data-controller="cookie-alert/extended/button/accept"]',
        // iWink / STARTER
        'body.cookies-request #cookie-bar .allow-cookies',
        // Real Cookie Banner (devowl.io)
        '.rcb-banner-cta-accept-all',
    ];

    // Generic accept button selectors (attribute-based)
    const genericAcceptSelectors = [
        'button[id*="accept" i]',
        'button[class*="accept-all" i]',
        'button[class*="acceptAll" i]',
        'a[id*="accept" i]',
        'button[id*="agree" i]',
        'button[class*="agree" i]',
        'button[class*="allow-all" i]',
        'button[class*="allowAll" i]',
        'button[data-action="accept"]',
        'button[data-action="accept-all"]',
        'button[data-gdpr="accept"]',
        'button[data-consent="accept"]',
    ];

    // Try clicking a CMP-specific accept button
    const clickButton = async (selectors) => {
        for (const selector of selectors) {
            try {
                const btn = document.querySelector(selector);
                if (btn && isVisible(btn)) {
                    btn.click();
                    await new Promise(r => setTimeout(r, 300));
                    return true;
                }
            } catch (e) { /* continue */ }
        }
        return false;
    };

    let accepted = await clickButton(cmpAcceptSelectors);
    if (!accepted) accepted = await clickButton(genericAcceptSelectors);

    // Text-content fallback: find buttons by visible text
    if (!accepted) {
        const acceptPatterns = [
            /^accept\s*(all)?(\s*cookies)?$/i,
            /^allow\s*(all)?(\s*cookies)?$/i,
            /^i\s*agree$/i,
            /^agree(\s*(and|&)\s*(close|continue))?$/i,
            /^got\s*it[!]?$/i,
            /^consent$/i,
            /^(accept|agree)\s*&?\s*close$/i,
        ];

        const candidates = document.querySelectorAll(
            'button, a[role="button"], [role="button"], input[type="submit"], input[type="button"]'
        );
        for (const btn of candidates) {
            const text = (btn.textContent || btn.value || '').trim();
            if (text.length > 0 && text.length < 40) {
                for (const pattern of acceptPatterns) {
                    if (pattern.test(text) && isVisible(btn)) {
                        btn.click();
                        accepted = true;
                        await new Promise(r => setTimeout(r, 300));
                        break;
                    }
                }
                if (accepted) break;
            }
        }
    }

    // Shadow DOM: Usercentrics, Axeptio
    if (!accepted) {
        const shadowRoots = [
            { id: 'usercentrics-root', btn: 'button[data-testid="uc-accept-all-button"]' },
            { cls: 'axeptio_mount', btn: 'button#axeptio_btn_acceptAll' },
        ];
        for (const cfg of shadowRoots) {
            try {
                const host = cfg.id
                    ? document.getElementById(cfg.id)
                    : document.querySelector('.' + cfg.cls);
                if (host && host.shadowRoot) {
                    const btn = host.shadowRoot.querySelector(cfg.btn);
                    if (btn) {
                        btn.click();
                        accepted = true;
                        await new Promise(r => setTimeout(r, 300));
                        break;
                    }
                }
            } catch (e) { /* continue */ }
        }
    }

    // Iframe-based CMPs (Sourcepoint, FastCMP, TrustArc, Privacy Manager)
    if (!accepted) {
        const iframeSelectors = [
            'iframe[id^="sp_message_iframe"]',
            'iframe#fast-cmp-iframe',
            'iframe[id*="consent" i]',
            'iframe[title*="consent" i]',
            'iframe[title*="cookie" i]',
            'iframe[title*="privacy" i]',
            'iframe[src*="privacymanager" i]',
            'iframe[src*="consent-tool" i]',
        ];
        for (const sel of iframeSelectors) {
            try {
                const iframe = document.querySelector(sel);
                if (iframe && iframe.contentDocument) {
                    const iframeDoc = iframe.contentDocument;
                    const btns = iframeDoc.querySelectorAll(
                        'button[title="Accept All" i], button[title="Accept" i], ' +
                        '.sp_choice_type_11, button.message-button, ' +
                        'button[class*="accept" i], button[class*="agree" i]'
                    );
                    for (const btn of btns) {
                        if (btn.offsetParent !== null) {
                            btn.click();
                            accepted = true;
                            await new Promise(r => setTimeout(r, 300));
                            break;
                        }
                    }
                    if (accepted) break;
                }
            } catch (e) { /* cross-origin iframes will throw SecurityError, expected */ }
        }
    }

    // =========================================================================
    // Phase 2: Try CMP JavaScript APIs
    // =========================================================================

    // IAB TCF v2 API
    if (typeof window.__tcfapi === 'function') {
        try {
            window.__tcfapi('addEventListener', 2, () => {});
        } catch (e) { /* continue */ }
    }

    // Didomi API
    if (typeof window.Didomi !== 'undefined') {
        try {
            window.Didomi.setUserAgreeToAll();
        } catch (e) { /* continue */ }
    }

    // Cookiebot API
    if (typeof window.Cookiebot !== 'undefined') {
        try {
            window.Cookiebot.submitCustomConsent(true, true, true);
        } catch (e) { /* continue */ }
    }

    // Osano API
    if (typeof window.Osano !== 'undefined') {
        try {
            window.Osano.cm.acceptAll();
        } catch (e) { /* continue */ }
    }

    // Klaro API
    if (typeof window.klaro !== 'undefined') {
        try {
            window.klaro.getManager().acceptAll();
        } catch (e) { /* continue */ }
    }

    // Wait for CMP animations/transitions
    await new Promise(r => setTimeout(r, 500));

    // =========================================================================
    // Phase 3: Remove known CMP containers by selector
    // =========================================================================
    const cmpContainerSelectors = [
        // --- Tier 1: Enterprise CMPs ---

        // OneTrust / CookiePro
        '#onetrust-consent-sdk',
        '#onetrust-banner-sdk',
        '.onetrust-pc-dark-filter',
        '#onetrust-pc-sdk',

        // Cookiebot (Usercentrics/Cybot)
        '#CybotCookiebotDialog',
        '#CybotCookiebotDialogBodyUnderlay',
        '#dtcookie-container',
        '#cookiebanner',

        // TrustArc
        '#truste-consent-track',
        '.truste_overlay',
        '.truste_box_overlay',
        '#truste-consent-content',
        '#consent_blackbar',
        '.trustarc-banner-container',

        // Quantcast Choice
        '.qc-cmp2-container',
        '#qc-cmp2-main',
        '.qc-cmp-cleanslate',

        // Didomi
        '#didomi-host',
        '#didomi-popup',
        '#didomi-notice',

        // Usercentrics
        '#usercentrics-root',
        '#usercentrics-cmp-ui',

        // Sourcepoint
        'div[id^="sp_message_container"]',
        '.sp_message_container',

        // Google FundingChoices / FC
        '.fc-consent-root',
        '.fc-dialog-overlay',
        '.fc-dialog-container',

        // --- Tier 2: Mid-Market CMPs ---

        // Klaro
        '.klaro',

        // Osano
        '.osano-cm-window',
        '.osano-cm-dialog',

        // Iubenda
        '#iubenda-cs-banner',

        // Complianz (WordPress)
        '.cmplz-cookiebanner',
        '#cmplz-cookiebanner-container',

        // CookieYes
        '.cky-consent-container',
        '.cky-overlay',

        // ConsentManager.net
        '.cmpbox',
        '#cmpbox',
        '#cmpbox2',
        '#cmpwrapper',

        // LiveRamp / Fides (Ethyca)
        '.fides-overlay',
        '#fides-banner',
        '#fides-overlay',
        '#fides-overlay-wrapper',

        // Termly
        '#termly-code-snippet-support',

        // CookieFirst
        '#cookiefirst-root',
        '.cookiefirst-root',

        // CookieScript
        '#cookiescript_injected',
        '.cookiescript_fsd_main',

        // Borlabs Cookie (WordPress)
        '#BorlabsCookieBox',
        '._brlbs-bar-wrap',
        '._brlbs-box-wrap',

        // Civic Cookie Control
        '#ccc',
        '#ccc-module',
        '#ccc-overlay',

        // Cookie Information
        '#cookie-information-template-wrapper',
        '#coiOverlay',

        // Evidon / Crownpeak
        '#_evidon_banner',
        '#_evidon-background',
        '#evidon-prefdiag-overlay',

        // Axeptio
        '.axeptio_widget',
        '.axeptio_mount',

        // HubSpot
        '#hs-eu-cookie-confirmation',

        // Ketch
        '#lanyard_root',

        // --- Tier 3: Regional / WordPress / Specialized CMPs ---

        // tarteaucitron.js
        '#tarteaucitronRoot',
        '#tarteaucitronAlertBig',

        // CookieHub
        '.ch2-container',
        '.ch2-dialog',

        // Moove GDPR (WordPress)
        '#moove_gdpr_cookie_info_bar',
        '#moove_gdpr_cookie_modal',
        '.gdpr_cookie_settings_popup_overlay',

        // TermsFeed
        '.termsfeed-com---nb',

        // Cookie Notice (WP plugin)
        '#cookie-notice',

        // Cookie Law Info / WebToffee
        '#cookie-law-info-bar',
        '#cookie-law-bg',
        '.cli-popupbar-overlay',

        // EU Cookie Compliance (Drupal)
        '.eu-cookie-compliance-banner',

        // WordPress GDPR Cookie Consent
        '#gdpr-cookie-consent-bar',

        // Shopify Native
        '#shopify-pc__banner',

        // Wix Native
        '[data-comp-type="cookie-banner-root-wix"]',
        '[data-hook="ccsu-banner-wrapper"]',

        // Finsweet (Webflow)
        '[fs-consent-element="banner"]',
        '.fs-cc-components',

        // Pandectes (Shopify)
        '#pandectes-banner',

        // Clickio
        '#cl-consent',

        // Snigel
        '.snigel-cmp-framework',

        // Cassie
        '.cassie-cookie-module',
        '.cassie-pre-banner',

        // FastCMP
        '#fast-cmp-root',

        // Sibbo
        'sibbo-cmp-layout',

        // PubTech
        '#pubtech-cmp',

        // UniConsent
        '.unic',

        // Ezoic
        '#ez-cookie-dialog-wrapper',

        // Transcend
        '#transcend-consent-manager',

        // Cloudflare Zaraz
        '.cf_modal_container',

        // CookieConsent v2 (Insites/Osano OSS)
        '#cc--main',

        // CookieConsent v3 (orestbida)
        '#cc-main',

        // Openli / Legal Monster
        '.legalmonster-cleanslate',

        // UK Cookie Consent (Catapult)
        '#catapult-cookie-bar',

        // Sirdata
        '#sd-cmp',

        // Mediavine
        '[data-name="mediavine-gdpr-cmp"]',

        // Consentmo (Shopify)
        '.isense-cc-window',

        // AdOpt
        '#cookie-banner',

        // Truyo
        '#truyo-consent-module',

        // KConsent
        '#kconsent',
        '.kc-overlay',

        // Gravito
        '.gravitoCMP-background-overlay',

        // CT Ultimate GDPR (WordPress)
        '#ct-ultimate-gdpr-cookie-popup',

        // Hu-manity
        '#hu.hu-wrapper',

        // GDPR Legal Cookie (Shopify)
        '.overlay_bc_banner',

        // Piwik PRO
        '.PiwikPROConsentForm-container',

        // Tealium
        '#__tealiumGDPRecModal',
        '#__tealiumImplicitmodal',
        '#consent-layer',

        // PMC (Penske Media)
        '#pmc-pp-tou--notice',

        // Privado
        '#cookie-consent-banner',

        // Real Cookie Banner (devowl.io)
        '.rcb-banner',

        // Bing / Microsoft
        '#bnp_container',
        '#bnp_cookie_banner',

        // LinkedIn
        '.artdeco-global-alert[type="COOKIE_CONSENT"]',

        // Privacy Manager
        '#gdpr-consent-tool-wrapper',

        // --- Generic patterns (catch-all) ---
        '[class*="cookie-consent" i]',
        '[id*="cookie-consent" i]',
        '[class*="cookie-banner" i]',
        '[id*="cookie-banner" i]',
        '[class*="consent-banner" i]',
        '[id*="consent-banner" i]',
        '[class*="consent-popup" i]',
        '[id*="consent-popup" i]',
        '[class*="gdpr-banner" i]',
        '[id*="gdpr-banner" i]',
        '[class*="cookie-notice" i]',
        '[id*="cookie-notice" i]',
        '[class*="cookie-law" i]',
        '[id*="cookie-law" i]',
        '[class*="cookie-popup" i]',
        '[id*="cookie-popup" i]',
        '[class*="cookie-overlay" i]',
        '[id*="cookie-overlay" i]',
        '.cc-banner',
        '.cc-window',
    ];

    for (const selector of cmpContainerSelectors) {
        try {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => el.remove());
        } catch (e) { /* continue */ }
    }

    // =========================================================================
    // Phase 4: Remove CMP iframes
    // =========================================================================
    const cmpIframeSelectors = [
        'iframe[id^="sp_message_iframe"]',
        'iframe#fast-cmp-iframe',
        'iframe[src*="consent" i]',
        'iframe[src*="cookie-cdn" i]',
        'iframe[src*="cookiebot" i]',
        'iframe[src*="trustarc" i]',
        'iframe[src*="consentmanager" i]',
        'iframe[src*="privacymanager" i]',
        'iframe[src*="cmp-consent-tool" i]',
        'iframe[title*="consent" i]',
        'iframe[title*="cookie" i]',
        'iframe[title*="gdpr" i]',
        'iframe[name="__tcfapiLocator"]',
    ];

    for (const selector of cmpIframeSelectors) {
        try {
            const iframes = document.querySelectorAll(selector);
            iframes.forEach(iframe => {
                // Also remove parent if it's a CMP wrapper (fixed/high-z)
                const parent = iframe.parentElement;
                if (parent && parent.children.length <= 2) {
                    const style = window.getComputedStyle(parent);
                    if (style.position === 'fixed' || style.position === 'absolute' ||
                        parseInt(style.zIndex) > 999) {
                        parent.remove();
                        return;
                    }
                }
                iframe.remove();
            });
        } catch (e) { /* continue */ }
    }

    // =========================================================================
    // Phase 5: Restore body scroll and clean up CMP artifacts
    // =========================================================================

    // Reset overflow on body and html
    document.body.style.overflow = '';
    document.body.style.overflowY = '';
    document.body.style.position = '';
    document.body.style.marginRight = '';
    document.body.style.paddingRight = '';
    document.documentElement.style.overflow = '';
    document.documentElement.style.overflowY = '';
    document.documentElement.style.position = '';

    // Remove known CMP body classes
    const cmpBodyClasses = [
        'ot-overflow-hidden',
        'sp_message_open',
        'didomi-popup-open',
        'cmpbox-show',
        'cmplz-blocked',
        'qc-cmp2-no-scroll',
        'osano-cm-show',
        'cky-modal-open',
        'fides-overlay-modal-open',
        'cc-no-scroll',
        'gdpr-cookie-notice-center-loaded',
        'fc-consent-root-open',
        'cookie-notification-active',
        'consent-bar-push-large',
        'with-eu-cookie-guideline',
        'cookies-request',
        'eu-cookie-compliance-popup-open',
        'has-cookie-bar',
    ];

    for (const cls of cmpBodyClasses) {
        document.body.classList.remove(cls);
        document.documentElement.classList.remove(cls);
    }
};
