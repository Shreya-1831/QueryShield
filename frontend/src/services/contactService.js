// Contact submissions remain local by default. Connect this function to a FastAPI contact endpoint if one is added.
export async function submitContact(formData) {
  const saved = { ...formData, createdAt: new Date().toISOString() };
  const previous = JSON.parse(localStorage.getItem('queryshield-contact-drafts') || '[]');
  localStorage.setItem('queryshield-contact-drafts', JSON.stringify([...previous, saved]));
  return {success: true, message: 'Your message was saved locally in this browser. No message was sent to a server.'};
}
