import { useEffect, useState } from "react";

/** Retrasa la propagación de `value` hasta que pase `delayMs` sin cambios —
 * evita disparar un fetch por cada tecla en inputs de búsqueda ligados a un
 * queryKey de react-query. */
export function useDebounce<T>(value: T, delayMs = 350): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}
