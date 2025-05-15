import { useState, useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

export default function LogViewer({ logs, maxMessages = 5 }) {
  const bottomRef = useRef(null);

  // Auto-scroll to the bottom whenever logs update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Calculate container height based on maxMessages (assuming ~24px per log line)
  const containerHeight = maxMessages * 29;

  return (
    <>
      <ScrollArea style={{ height: `${containerHeight}px` }} className="w-full pr-2 rounded-md border border-neutral-200 dark:border-neutral-700 bg-neutral-100 dark:bg-neutral-800">
        <ul className="text-sm space-y-1 space-x-2">
          {logs.map((log, index) => (
            <li
              key={index}
              className={`pt-0 pb-0 ${
                log.type === "error" ? "text-red-500 font-semibold" : "text-foreground"
              }`}
            >
              {log.message}
              {index !== logs.length - 1 && <Separator className="mt-1 mb-0 bg-muted-foreground max-w-[100%]" />}
            </li>
          ))}
          {/* Dummy element to scroll into view */}
          <div ref={bottomRef} />
        </ul>
      </ScrollArea>
    </>
  );
}