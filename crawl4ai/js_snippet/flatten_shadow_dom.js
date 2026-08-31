/**
 * Flatten all open shadow DOM trees into the light DOM so that
 * page.content() / outerHTML can serialize the full composed view.
 *
 * Uses manual recursive serialization with proper slot resolution.
 * Resolves slots via the live DOM API (assignedNodes), skips only
 * shadow-scoped styles, and produces clean HTML with no regex hacks.
 *
 * Returns the full HTML string including shadow content.
 */
(() => {
    const VOID = new Set([
        'area','base','br','col','embed','hr','img','input',
        'link','meta','param','source','track','wbr'
    ]);

    // Serialize a DOM node. When it has a shadow root, switch to
    // shadow-aware serialization that resolves <slot> elements.
    const serialize = (node) => {
        if (node.nodeType === Node.TEXT_NODE) return node.textContent;
        if (node.nodeType === Node.COMMENT_NODE) return '';
        if (node.nodeType !== Node.ELEMENT_NODE) return '';

        const tag = node.tagName.toLowerCase();
        const attrs = serializeAttrs(node);
        let inner = '';

        if (node.shadowRoot) {
            inner = serializeShadowRoot(node);
        } else {
            for (const child of node.childNodes) {
                inner += serialize(child);
            }
        }

        if (VOID.has(tag)) return `<${tag}${attrs}>`;
        return `<${tag}${attrs}>${inner}</${tag}>`;
    };

    // Serialize a shadow root's children, resolving slots against
    // the host's light DOM children.
    const serializeShadowRoot = (host) => {
        let result = '';
        for (const child of host.shadowRoot.childNodes) {
            result += serializeShadowChild(child, host);
        }
        return result;
    };

    // Serialize a node that lives inside a shadow root.
    // <style> tags are skipped (scoped CSS, useless outside shadow).
    // <slot> tags are replaced with their assigned (projected) nodes.
    const serializeShadowChild = (node, host) => {
        if (node.nodeType === Node.TEXT_NODE) return node.textContent;
        if (node.nodeType === Node.COMMENT_NODE) return '';
        if (node.nodeType !== Node.ELEMENT_NODE) return '';

        const tag = node.tagName.toLowerCase();

        // Skip shadow-scoped styles only
        if (tag === 'style') return '';

        // Resolve <slot>: replace with projected light DOM content
        if (tag === 'slot') {
            const assigned = node.assignedNodes({ flatten: true });
            if (assigned.length > 0) {
                let out = '';
                for (const a of assigned) out += serialize(a);
                return out;
            }
            // No assigned nodes — use the slot's fallback content
            let fallback = '';
            for (const child of node.childNodes) {
                fallback += serializeShadowChild(child, host);
            }
            return fallback;
        }

        const attrs = serializeAttrs(node);
        let inner = '';

        if (node.shadowRoot) {
            // Nested shadow root — recurse
            inner = serializeShadowRoot(node);
        } else {
            for (const child of node.childNodes) {
                inner += serializeShadowChild(child, host);
            }
        }

        if (VOID.has(tag)) return `<${tag}${attrs}>`;
        return `<${tag}${attrs}>${inner}</${tag}>`;
    };

    const serializeAttrs = (node) => {
        let s = '';
        for (const a of node.attributes || []) {
            s += ` ${a.name}="${a.value.replace(/&/g, '&amp;').replace(/"/g, '&quot;')}"`;
        }
        return s;
    };

    return serialize(document.documentElement);
})()
