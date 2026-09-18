import { useMemo, useState } from "react";

const DEFAULT_PAGE_SIZES = [25, 50, 100];

export function usePagination<T>(items: T[], initialPageSize: number = DEFAULT_PAGE_SIZES[0]) {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSizeState] = useState(initialPageSize);

  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
  const effectivePage = Math.min(page, totalPages - 1);
  const pageItems = useMemo(
    () => items.slice(effectivePage * pageSize, (effectivePage + 1) * pageSize),
    [items, effectivePage, pageSize]
  );

  const setPageSize = (size: number) => {
    setPageSizeState(size);
    setPage(0);
  };

  return { page: effectivePage, setPage, pageSize, setPageSize, pageItems, totalPages };
}

export { DEFAULT_PAGE_SIZES };
