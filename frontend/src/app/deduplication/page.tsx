import { redirect } from "next/navigation";

export default function DeduplicationRedirect() {
  redirect("/inventory");
}
