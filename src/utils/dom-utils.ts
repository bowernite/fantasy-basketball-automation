/**
 * Gets the form that contains the submit button.
 * @param submitButton - The submit button to get the form for.
 * @returns The form that contains the submit button, or null if no form is found.
 */
export function getSubmitButtonForm(
  submitButton: HTMLButtonElement | HTMLInputElement
): HTMLFormElement | null {
  const directForm = submitButton.form;
  if (directForm instanceof HTMLFormElement) return directForm;

  const closestForm = submitButton.closest("form");
  if (closestForm instanceof HTMLFormElement) return closestForm;

  return null;
}


