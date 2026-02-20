"use client";

import { useState, useRef, type DragEvent } from "react";
import {
  type UseCaseResponse,
  type UseCaseStatus,
  updateUseCaseStatus,
} from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { GripVertical, Zap } from "lucide-react";

const KANBAN_COLUMNS: { status: UseCaseStatus; label: string }[] = [
  { status: "new", label: "New" },
  { status: "under_review", label: "Under Review" },
  { status: "approved", label: "Approved" },
  { status: "in_progress", label: "In Progress" },
  { status: "completed", label: "Completed" },
  { status: "archived", label: "Archived" },
];

interface KanbanBoardProps {
  useCases: UseCaseResponse[];
  onCardClick: (uc: UseCaseResponse) => void;
  onRefresh: () => void;
}

export function KanbanBoard({
  useCases,
  onCardClick,
  onRefresh,
}: KanbanBoardProps) {
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [overColumn, setOverColumn] = useState<UseCaseStatus | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);
  const dragCounters = useRef<Map<string, number>>(new Map());

  function handleDragStart(e: DragEvent, uc: UseCaseResponse) {
    setDraggedId(uc.id);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", uc.id);
    // Slight delay to let the ghost image appear
    requestAnimationFrame(() => {
      const el = document.getElementById(`card-${uc.id}`);
      if (el) el.style.opacity = "0.4";
    });
  }

  function handleDragEnd() {
    if (draggedId) {
      const el = document.getElementById(`card-${draggedId}`);
      if (el) el.style.opacity = "1";
    }
    setDraggedId(null);
    setOverColumn(null);
    dragCounters.current.clear();
  }

  function handleColumnDragEnter(e: DragEvent, status: UseCaseStatus) {
    e.preventDefault();
    const count = (dragCounters.current.get(status) || 0) + 1;
    dragCounters.current.set(status, count);
    setOverColumn(status);
  }

  function handleColumnDragLeave(status: UseCaseStatus) {
    const count = (dragCounters.current.get(status) || 0) - 1;
    dragCounters.current.set(status, count);
    if (count <= 0) {
      dragCounters.current.set(status, 0);
      if (overColumn === status) setOverColumn(null);
    }
  }

  function handleColumnDragOver(e: DragEvent) {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  }

  async function handleDrop(e: DragEvent, targetStatus: UseCaseStatus) {
    e.preventDefault();
    setOverColumn(null);
    dragCounters.current.clear();

    const ucId = e.dataTransfer.getData("text/plain");
    if (!ucId) return;

    const uc = useCases.find((u) => u.id === ucId);
    if (!uc || uc.status === targetStatus) {
      handleDragEnd();
      return;
    }

    setUpdating(ucId);
    try {
      await updateUseCaseStatus(ucId, targetStatus);
      onRefresh();
    } catch {
      // silent
    } finally {
      setUpdating(null);
      handleDragEnd();
    }
  }

  const grouped = KANBAN_COLUMNS.map((col) => ({
    ...col,
    items: useCases.filter((uc) => uc.status === col.status),
  }));

  if (useCases.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-foreground/10 py-16">
        <Zap className="mb-4 h-10 w-10 text-muted-foreground/50" />
        <p className="mb-1 font-medium">No use cases yet</p>
        <p className="text-sm text-muted-foreground">
          Upload transcripts to trigger AI use case extraction
        </p>
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <ScrollArea className="h-full w-full">
        <div className="flex h-full min-h-full gap-4 pb-4" style={{ minWidth: "fit-content" }}>
          {grouped.map((col) => {
            const isOver = overColumn === col.status && draggedId !== null;
            return (
              <div
                key={col.status}
                className={`flex h-full min-h-0 w-64 shrink-0 flex-col rounded-lg border transition-colors ${
                isOver
                  ? "border-foreground/40 bg-foreground/5"
                  : "border-foreground/10 bg-background"
              }`}
              onDragEnter={(e) => handleColumnDragEnter(e, col.status)}
              onDragLeave={() => handleColumnDragLeave(col.status)}
              onDragOver={handleColumnDragOver}
              onDrop={(e) => handleDrop(e, col.status)}
            >
              {/* Column header — sticky when scrolling cards */}
              <div className="sticky top-0 z-10 flex shrink-0 items-center justify-between border-b border-foreground/10 bg-background px-3 py-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-foreground">
                    {col.label}
                  </span>
                </div>
                <Badge
                  variant="secondary"
                  className="h-5 min-w-[20px] justify-center px-1.5 text-xs font-mono"
                >
                  {col.items.length}
                </Badge>
              </div>

              {/* Cards — scrollable */}
              <ScrollArea className="flex-1 min-h-0">
              <div className="flex flex-col gap-2 p-2" style={{ minHeight: 120 }}>
                {col.items.map((uc) => {
                  const isDragging = draggedId === uc.id;
                  const isUpdating = updating === uc.id;
                  return (
                    <div
                      id={`card-${uc.id}`}
                      key={uc.id}
                      draggable={!isUpdating}
                      onDragStart={(e) => handleDragStart(e, uc)}
                      onDragEnd={handleDragEnd}
                      onClick={() => onCardClick(uc)}
                      className={`group cursor-pointer rounded-md border border-foreground/10 bg-background p-3 shadow-sm transition-all hover:border-foreground/30 hover:shadow-md ${
                        isDragging ? "opacity-40" : ""
                      } ${isUpdating ? "animate-pulse opacity-60" : ""}`}
                    >
                      {/* Card handle + ID */}
                      <div className="mb-2 flex items-center gap-1.5">
                        <GripVertical className="h-3.5 w-3.5 shrink-0 text-muted-foreground/40 opacity-0 transition-opacity group-hover:opacity-100" />
                        <span className="font-mono text-[10px] text-muted-foreground">
                          UC-{uc.id.slice(0, 6).toUpperCase()}
                        </span>
                        {uc.confidence_score > 0 && (
                          <Badge className="ml-auto h-4 bg-foreground/10 px-1 text-[10px] text-foreground">
                            {Math.round(uc.confidence_score * 100)}%
                          </Badge>
                        )}
                      </div>

                      {/* Title */}
                      <h4 className="mb-1.5 line-clamp-2 text-sm font-medium leading-snug text-foreground">
                        {uc.title}
                      </h4>

                      {/* Description preview */}
                      <p className="mb-2 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                        {uc.description}
                      </p>

                      {/* Tags */}
                      {uc.tags && uc.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {uc.tags.slice(0, 3).map((tag, i) => (
                            <span
                              key={i}
                              className="rounded-sm bg-foreground/5 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                            >
                              {tag}
                            </span>
                          ))}
                          {uc.tags.length > 3 && (
                            <span className="rounded-sm bg-foreground/5 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                              +{uc.tags.length - 3}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Footer: priority + scores */}
                      {(uc.priority_score !== null || uc.impact_score !== null) && (
                        <div className="mt-2 flex items-center gap-2 border-t border-foreground/5 pt-2 text-[10px] text-muted-foreground">
                          {uc.priority_score !== null && (
                            <span>Priority: {uc.priority_score.toFixed(1)}</span>
                          )}
                          {uc.impact_score !== null && (
                            <span>Impact: {uc.impact_score}/5</span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}

                {/* Drop zone placeholder */}
                {isOver && col.items.length === 0 && (
                  <div className="flex items-center justify-center rounded-md border-2 border-dashed border-foreground/20 py-8">
                    <p className="text-xs text-muted-foreground">Drop here</p>
                  </div>
                )}
              </div>
              </ScrollArea>
            </div>
          );
        })}
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  );
}
