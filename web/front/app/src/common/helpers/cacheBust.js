
/**
 * Добавляет уникальный query-параметр для сброса кэша
 * @param {string} url - URL ресурса
 * @param {string} [param="v"] - имя query-параметра
 * @returns {string} - URL с уникальным параметром
 */
export function cacheBustUrl(url, param = "v") {
  if (!url) return url;
  // Проверяем, есть ли уже такой параметр
  const re = new RegExp(`[?&]${param}=`);
  if (re.test(url)) {
    return url; // уже есть, не добавляем
  }
  const sep = url.includes('?') ? '&' : '?';
  return url + sep + param + '=' + Date.now();
}