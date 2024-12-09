import { getPageDate } from "./page/page-querying";

export function getNumDaysInFuture() {
  const pageDate = getPageDate();
  const today = new Date(new Date().setHours(0, 0, 0, 0));
  const diffInMs = pageDate.getTime() - today.getTime();
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
  return diffInDays;
}
