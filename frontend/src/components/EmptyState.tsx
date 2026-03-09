import { Inbox } from "lucide-react";

interface Props {
  message: string;
}

export function EmptyState({ message }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Inbox className="w-10 h-10 text-cream-faint/40 mb-3" />
      <p className="text-sm text-cream-faint">{message}</p>
    </div>
  );
}
