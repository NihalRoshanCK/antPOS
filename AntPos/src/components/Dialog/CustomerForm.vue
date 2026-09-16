<template>
  <Dialog :options="{ title: 'New customer', size: '2xl' }" v-model="dialogVisible" @after-leave="handleDialogClose">
    <template #body-content>
      <!-- Fields come from the "Customer / Quick Entry" layout
           (Antpos Fields Layout), so an admin decides what is asked here. -->
      <form id="pos-customer-form" novalidate @submit.prevent="submit">
        <LayoutForm
          :layout="layout"
          :doc="customer"
          :show-errors="showErrors"
          id-prefix="customer"
        />
        <p v-if="showErrors && missing.length" class="mt-4 text-sm text-ink-red-4" role="alert">
          Fill in {{ missing.join(', ') }}.
        </p>
      </form>
    </template>

    <template #actions>
      <div class="flex flex-row-reverse gap-2">
        <Button
          variant="solid"
          type="submit"
          form="pos-customer-form"
          class="flex-1 sm:flex-none"
          :loading="createCustomer.loading"
          :disabled="layout.loading || Boolean(layout.error)"
        >
          Create customer
        </Button>
        <Button class="flex-1 sm:flex-none" @click="handleDialogClose">Cancel</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { Dialog, Button, createResource } from 'frappe-ui';
import emitter from '@/utils/emitter';
import { showToast } from '@/utils';
import LayoutForm from '@/components/form/LayoutForm.vue';
import { applyDefaults, missingRequired, useFormLayout } from '@/utils/formLayout';

const dialogVisible = ref(true);
const layout = useFormLayout('Customer', 'Quick Entry');
const customer = reactive({});
const showErrors = ref(false);

// Defaults (e.g. customer type "Individual") fill in once the layout is known.
watch(() => layout.sections, (sections) => applyDefaults(sections, customer), { immediate: true });

const missing = computed(() => missingRequired(layout.sections, customer));

const handleDialogClose = () => {
  dialogVisible.value = false;
};

const createCustomer = createResource({
  url: 'ant_pos.ant_pos.api.form_layout.create_from_quick_entry',
  method: 'POST',
  makeParams: () => ({ doctype: 'Customer', doc: JSON.stringify(customer) }),
  onSuccess(data) {
    emitter.emit('customerCreated', data);
    showToast('success', 'New Customer Created');
    handleDialogClose();
  },
  onError(err) {
    showToast(
      'error',
      Array.isArray(err?.messages) ? err.messages[0] : err?.messages || 'Could not create customer',
      'x-circle'
    );
  },
});

function submit() {
  showErrors.value = true;
  if (missing.value.length || createCustomer.loading) return;
  createCustomer.fetch();
}
</script>
