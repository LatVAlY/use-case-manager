"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  listComments,
  createComment,
  deleteComment,
  updateUseCaseStatus,
  updateUseCaseScores,
  deleteUseCase,
  type UseCaseResponse,
  type UseCaseStatus,
  type CommentResponse,
  type UseCaseScoresUpdate,
} from "@/lib/api-client";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Spinner } from "@/components/ui/spinner";
import {
  Trash2,
  Send,
  TrendingUp,
  Tag,
  MessageSquare,
  Clock,
  User,
} from "lucide-react";

const STATUS_OPTIONS: UseCaseStatus[] = [
  "new",
  "under_review",
  "approved",
  "in_progress",
  "completed",
  "archived",
];

function statusLabel(status: string) {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

interface UseCaseDetailDialogProps {
  useCase: UseCaseResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onStatusChange: (id: string, status: UseCaseStatus) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onUpdate: () => void;
}

export function UseCaseDetailDialog({
  useCase,
  open,
  onOpenChange,
  onStatusChange,
  onDelete,
  onUpdate,
}: UseCaseDetailDialogProps) {
  const [comments, setComments] = useState<CommentResponse[]>([]);
  const [loadingComments, setLoadingComments] = useState(false);
  const [newComment, setNewComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState<"details" | "comments">("details");
  const [scores, setScores] = useState<UseCaseScoresUpdate>({});
  const [savingScores, setSavingScores] = useState(false);
  const commentsEndRef = useRef<HTMLDivElement>(null);

  const fetchComments = useCallback(async () => {
    if (!useCase) return;
    setLoadingComments(true);
    try {
      const res = await listComments(useCase.id);
      setComments(res.items || []);
    } catch {
      // silent
    } finally {
      setLoadingComments(false);
    }
  }, [useCase]);

  useEffect(() => {
    if (open && useCase) {
      fetchComments();
      setScores({
        effort_score: useCase.effort_score ?? undefined,
        impact_score: useCase.impact_score ?? undefined,
        complexity_score: useCase.complexity_score ?? undefined,
        strategic_score: useCase.strategic_score ?? undefined,
      });
    }
  }, [open, useCase, fetchComments]);

  useEffect(() => {
    if (commentsEndRef.current) {
      commentsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [comments]);

  async function handleSubmitComment() {
    if (!useCase || !newComment.trim()) return;
    setSubmitting(true);
    try {
      await createComment(useCase.id, newComment.trim());
      setNewComment("");
      await fetchComments();
    } catch {
      // silent
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteComment(commentId: string) {
    if (!useCase) return;
    try {
      await deleteComment(useCase.id, commentId);
      await fetchComments();
    } catch {
      // silent
    }
  }

  async function handleSaveScores() {
    if (!useCase) return;
    setSavingScores(true);
    try {
      await updateUseCaseScores(useCase.id, scores);
      onUpdate();
    } catch {
      // silent
    } finally {
      setSavingScores(false);
    }
  }

  async function handleDelete() {
    if (!useCase) return;
    await onDelete(useCase.id);
    onOpenChange(false);
  }

  if (!useCase) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] max-w-3xl flex-col border-foreground/10 p-0 sm:max-w-3xl">
        {/* Header */}
        <DialogHeader className="space-y-3 border-b border-foreground/10 px-6 pt-6 pb-4">
          <div className="flex items-start justify-between gap-4 pr-8">
            <div className="min-w-0 flex-1">
              <div className="mb-2 flex items-center gap-2">
                <Badge variant="outline" className="border-foreground/20 text-xs font-mono">
                  UC-{useCase.id.slice(0, 6).toUpperCase()}
                </Badge>
                {useCase.confidence_score > 0 && (
                  <Badge className="bg-foreground/10 text-xs text-foreground">
                    {Math.round(useCase.confidence_score * 100)}% confidence
                  </Badge>
                )}
              </div>
              <DialogTitle className="text-xl font-bold leading-tight text-balance">
                {useCase.title}
              </DialogTitle>
            </div>
          </div>
          {/* Status selector in header */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">Status:</span>
            <Select
              value={useCase.status}
              onValueChange={(val) => onStatusChange(useCase.id, val as UseCaseStatus)}
            >
              <SelectTrigger className="h-7 w-40 border-foreground/20 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map((s) => (
                  <SelectItem key={s} value={s} className="text-xs">
                    {statusLabel(s)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </DialogHeader>

        {/* Tab bar */}
        <div className="flex border-b border-foreground/10 px-6">
          <button
            onClick={() => setActiveTab("details")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "details"
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <TrendingUp className="h-4 w-4" />
            Details
          </button>
          <button
            onClick={() => setActiveTab("comments")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "comments"
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            Comments
            {comments.length > 0 && (
              <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                {comments.length}
              </Badge>
            )}
          </button>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1 overflow-auto">
          <div className="px-6 py-4">
            {activeTab === "details" ? (
              <div className="space-y-6">
                {/* Description */}
                <div className="space-y-2">
                  <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Description
                  </h3>
                  <p className="text-sm leading-relaxed text-foreground">
                    {useCase.description}
                  </p>
                </div>

                {/* Expected Benefit */}
                {useCase.expected_benefit && (
                  <div className="space-y-2">
                    <h3 className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      <TrendingUp className="h-3.5 w-3.5" />
                      Expected Benefit
                    </h3>
                    <p className="text-sm leading-relaxed text-foreground">
                      {useCase.expected_benefit}
                    </p>
                  </div>
                )}

                {/* Tags */}
                {useCase.tags && useCase.tags.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      <Tag className="h-3.5 w-3.5" />
                      Tags
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {useCase.tags.map((tag, i) => (
                        <Badge
                          key={i}
                          variant="outline"
                          className="border-foreground/20 text-xs"
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <Separator className="bg-foreground/10" />

                {/* Scores */}
                <div className="space-y-3">
                  <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Scores
                  </h3>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {(
                      [
                        { key: "effort_score", label: "Effort" },
                        { key: "impact_score", label: "Impact" },
                        { key: "complexity_score", label: "Complexity" },
                        { key: "strategic_score", label: "Strategic" },
                      ] as const
                    ).map(({ key, label }) => (
                      <div
                        key={key}
                        className="rounded-md border border-foreground/10 p-3"
                      >
                        <p className="mb-1 text-xs text-muted-foreground">
                          {label}
                        </p>
                        <Select
                          value={
                            scores[key] !== undefined && scores[key] !== null
                              ? String(scores[key])
                              : "unset"
                          }
                          onValueChange={(val) =>
                            setScores((prev) => ({
                              ...prev,
                              [key]: val === "unset" ? null : Number(val),
                            }))
                          }
                        >
                          <SelectTrigger className="h-8 border-foreground/10 text-sm">
                            <SelectValue placeholder="--" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="unset">--</SelectItem>
                            {[1, 2, 3, 4, 5].map((n) => (
                              <SelectItem key={n} value={String(n)}>
                                {n}/5
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ))}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSaveScores}
                    disabled={savingScores}
                    className="border-foreground/20"
                  >
                    {savingScores ? <Spinner className="mr-2" /> : null}
                    Save Scores
                  </Button>
                </div>

                {useCase.priority_score !== null &&
                  useCase.priority_score !== undefined && (
                    <div className="rounded-md border border-foreground/10 p-4">
                      <p className="text-xs text-muted-foreground">
                        Priority Score
                      </p>
                      <p className="text-2xl font-bold text-foreground">
                        {useCase.priority_score.toFixed(1)}
                      </p>
                    </div>
                  )}

                <Separator className="bg-foreground/10" />

                {/* Meta */}
                <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    Created {new Date(useCase.created_at).toLocaleString()}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    Updated {new Date(useCase.updated_at).toLocaleString()}
                  </span>
                  {useCase.assignee_id && (
                    <span className="flex items-center gap-1">
                      <User className="h-3.5 w-3.5" />
                      Assignee: {useCase.assignee_id.slice(0, 8)}
                    </span>
                  )}
                </div>

                {/* Delete */}
                <div className="flex justify-end">
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <Trash2 className="mr-1 h-4 w-4" />
                        Delete Use Case
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent className="border-foreground/10">
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete use case?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This will permanently remove this use case.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={handleDelete}
                          className="bg-foreground text-background hover:bg-foreground/90"
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            ) : (
              /* Comments tab */
              <div className="flex h-[400px] flex-col">
                <div className="flex-1 space-y-4 overflow-y-auto pb-4">
                  {loadingComments ? (
                    <div className="flex items-center justify-center py-8">
                      <Spinner />
                    </div>
                  ) : comments.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                      <MessageSquare className="mb-3 h-8 w-8 opacity-40" />
                      <p className="text-sm">No comments yet</p>
                      <p className="text-xs">
                        Start the conversation below
                      </p>
                    </div>
                  ) : (
                    comments.map((comment) => (
                      <div
                        key={comment.id}
                        className="group flex gap-3"
                      >
                        <Avatar className="h-8 w-8 shrink-0">
                          <AvatarFallback className="bg-foreground/10 text-xs font-medium text-foreground">
                            {comment.author_id.slice(0, 2).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium font-mono text-foreground">
                              {comment.author_id.slice(0, 8)}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(comment.created_at).toLocaleString()}
                            </span>
                            <button
                              onClick={() => handleDeleteComment(comment.id)}
                              className="ml-auto hidden text-muted-foreground hover:text-foreground group-hover:block"
                              title="Delete comment"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                          <p className="mt-1 text-sm leading-relaxed text-foreground">
                            {comment.body}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={commentsEndRef} />
                </div>

                {/* Comment input */}
                <div className="border-t border-foreground/10 pt-4">
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Add a comment..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                          handleSubmitComment();
                        }
                      }}
                      className="min-h-[60px] resize-none border-foreground/10 text-sm"
                    />
                    <Button
                      onClick={handleSubmitComment}
                      disabled={!newComment.trim() || submitting}
                      size="sm"
                      className="h-auto bg-foreground text-background hover:bg-foreground/90"
                    >
                      {submitting ? (
                        <Spinner />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Press Ctrl+Enter to send
                  </p>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
