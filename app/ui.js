export const $ = selector => document.querySelector(selector);
export function node(tag, text, className) {
  const item = document.createElement(tag);
  if (text !== undefined) item.textContent = text;
  if (className) item.className = className;
  return item;
}
export function options(select, entries) {
  select.replaceChildren(...entries.map(([id, title]) => {
    const option = node('option', title); option.value = id; return option;
  }));
}
export async function json(path, init) {
  const response = await fetch(path, init);
  const result = await response.json();
  if (!response.ok) {
    const error = new Error(result.error || 'The request could not be completed.');
    error.code = result.code || 'request_failed'; throw error;
  }
  return result;
}
