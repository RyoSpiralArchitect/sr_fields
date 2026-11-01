// Pure selection operations shared by the UI and offline behavior tests.
export function validFields(values, ids) {
  return Array.isArray(values) && values.every(id => typeof id === 'string' && ids.includes(id)) && new Set(values).size === values.length;
}
export function restoreComposition(saved, ids) {
  return {fields: validFields(saved?.fields, ids) ? [...saved.fields] : [...ids],
    language: ['en', 'ja'].includes(saved?.language) ? saved.language : 'en',
    mode: ['baseline', 'plain', 'structured'].includes(saved?.mode) ? saved.mode : 'structured'};
}
export function toggleField(fields, id) {
  return fields.includes(id) ? fields.filter(value => value !== id) : [...fields, id];
}
export function moveField(fields, id, delta) {
  const copy = [...fields], index = copy.indexOf(id), next = index + delta;
  if (index >= 0 && next >= 0 && next < copy.length) [copy[index], copy[next]] = [copy[next], copy[index]];
  return copy;
}
