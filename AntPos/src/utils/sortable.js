import Sortable from 'sortablejs';

// v-sortable="options": SortableJS on the element, created on mount and
// destroyed on unmount. Handlers are read at event time, so they always see
// the latest options.
//
// Sortable moves DOM nodes itself, which Vue does not know about. Callers
// should read the new order from the DOM in onEnd/onAdd and then re-render
// the list from state (e.g. by changing its :key), so Vue owns the DOM again.
const EVENTS = ['onStart', 'onEnd', 'onAdd', 'onUpdate', 'onRemove', 'onMove', 'onChoose', 'onUnchoose'];

export const vSortable = {
    mounted(el, binding) {
        el.__sortableOptions = binding.value || {};
        const handlers = Object.fromEntries(
            EVENTS.map((name) => [name, (...args) => el.__sortableOptions[name]?.(...args)])
        );
        const rest = { ...el.__sortableOptions };
        for (const name of EVENTS) delete rest[name];
        el.__sortable = Sortable.create(el, {
            animation: 150,
            // Touch: a short press starts a drag, so the page still scrolls.
            delay: 180,
            delayOnTouchOnly: true,
            ...rest,
            ...handlers,
        });
    },
    updated(el, binding) {
        el.__sortableOptions = binding.value || {};
        if (el.__sortable && 'disabled' in el.__sortableOptions) {
            el.__sortable.option('disabled', Boolean(el.__sortableOptions.disabled));
        }
    },
    unmounted(el) {
        el.__sortable?.destroy();
        el.__sortable = null;
    },
};
