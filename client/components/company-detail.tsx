"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  getCompany,
  listTranscripts,
  listUseCases,
  uploadTranscript,
  deleteTranscript,
  reprocessTranscript,
  deleteUseCase,
  updateUseCaseStatus,
  type CompanyResponse,
  type TranscriptResponse,
  type UseCaseResponse,
  type UseCaseStatus,
} from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowLeft,
  Upload,
  FileText,
  Trash2,
  ListChecks,
  RefreshCw,
} from "lucide-react";
import { KanbanBoard } from "@/components/kanban-board";
import { UseCaseDetailDialog } from "./use-case-dialog";

function statusLabel(status: string) {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function transcriptStatusBadge(status: string) {
  switch (status) {
    case "completed":
      return "bg-foreground text-background";
    case "processing":
      return "bg-foreground/60 text-background";
    case "failed":
      return "bg-foreground/30 text-foreground";
    default:
      return "bg-foreground/10 text-foreground";
  }
}

interface CompanyDetailProps {
  companyId: string;
}

export function CompanyDetail({ companyId }: CompanyDetailProps) {
  const [company, setCompany] = useState<CompanyResponse | null>(null);
  const [transcripts, setTranscripts] = useState<TranscriptResponse[]>([]);
  const [useCases, setUseCases] = useState<UseCaseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [selectedUseCase, setSelectedUseCase] = useState<UseCaseResponse | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const fetchData = useCallback(async () => {
    try {
      const [comp, trRes, ucRes] = await Promise.all([
        getCompany(companyId),
        listTranscripts(1, 100, companyId),
        listUseCases({ company_id: companyId }),
      ]);
      setCompany(comp);
      setTranscripts(trRes.items || []);
      setUseCases(ucRes.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await uploadTranscript(file, companyId);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDeleteTranscript(id: string) {
    try {
      await deleteTranscript(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function handleReprocess(id: string) {
    try {
      await reprocessTranscript(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reprocess failed");
    }
  }

  async function handleDeleteUseCase(id: string) {
    try {
      await deleteUseCase(id);
      setDialogOpen(false);
      setSelectedUseCase(null);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function handleStatusChange(id: string, status: UseCaseStatus) {
    try {
      await updateUseCaseStatus(id, status);
      // Keep the selected use case in sync so the dialog reflects the new status
      setSelectedUseCase((prev) =>
        prev?.id === id ? { ...prev, status } : prev
      );
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed");
    }
  }

  function handleCardClick(uc: UseCaseResponse) {
    setSelectedUseCase(uc);
    setDialogOpen(true);
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-40 w-full rounded-lg" />
        <Skeleton className="h-40 w-full rounded-lg" />
      </div>
    );
  }

  if (!company) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <p className="mb-4 text-muted-foreground">Company not found</p>
        <Button variant="outline" onClick={() => router.push("/dashboard")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/dashboard")}
          className="text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-bold tracking-tight">{company.name}</h1>
        {company.description && (
          <p className="mt-1 text-muted-foreground">{company.description}</p>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          Created {new Date(company.created_at).toLocaleDateString()}
          {company.website && (
            <>
              {" | "}
              <a
                href={company.website}
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                {company.website}
              </a>
            </>
          )}
        </p>
      </div>

      {error && (
        <div className="rounded-md border border-foreground/20 bg-foreground/5 px-4 py-3 text-sm text-foreground">
          {error}
          <button onClick={() => setError("")} className="ml-2 underline">
            dismiss
          </button>
        </div>
      )}

      <Tabs defaultValue="transcripts" className="w-full">
        <TabsList className="w-full justify-start bg-foreground/5">
          <TabsTrigger value="transcripts" className="gap-2">
            <FileText className="h-4 w-4" />
            Transcripts
            <Badge variant="secondary" className="ml-1">
              {transcripts.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="use-cases" className="gap-2">
            <ListChecks className="h-4 w-4" />
            Use Cases
            <Badge variant="secondary" className="ml-1">
              {useCases.length}
            </Badge>
          </TabsTrigger>
        </TabsList>

        {/* Transcripts */}
        <TabsContent value="transcripts" className="mt-6 space-y-4">
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.doc,.docx,.pdf"
              onChange={handleUpload}
              className="hidden"
              id="transcript-upload"
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              variant="outline"
              className="border-foreground/20"
            >
              {uploading ? (
                <Spinner className="mr-2" />
              ) : (
                <Upload className="mr-2 h-4 w-4" />
              )}
              Upload Transcript
            </Button>
          </div>

          {transcripts.length === 0 ? (
            <Card className="border-dashed border-foreground/10">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileText className="mb-4 h-10 w-10 text-muted-foreground/50" />
                <p className="mb-1 font-medium">No transcripts uploaded</p>
                <p className="text-sm text-muted-foreground">
                  Upload a workshop transcript to trigger AI extraction
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {transcripts.map((transcript) => (
                <Card key={transcript.id} className="border-foreground/10">
                  <CardHeader className="flex flex-row items-center justify-between py-4">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <CardTitle className="text-sm font-medium">
                          {transcript.filename}
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Uploaded {new Date(transcript.created_at).toLocaleString()}
                          {transcript.chunk_count !== null &&
                            ` | ${transcript.chunks_processed}/${transcript.chunk_count} chunks`}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={`text-xs ${transcriptStatusBadge(transcript.status)}`}>
                        {statusLabel(transcript.status)}
                      </Badge>
                      {transcript.status === "failed" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                          onClick={() => handleReprocess(transcript.id)}
                          title="Reprocess"
                        >
                          <RefreshCw className="h-4 w-4" />
                          <span className="sr-only">Reprocess</span>
                        </Button>
                      )}
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Delete transcript</span>
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent className="border-foreground/10">
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete transcript?</AlertDialogTitle>
                            <AlertDialogDescription>
                              This will permanently remove this transcript.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteTranscript(transcript.id)}
                              className="bg-foreground text-background hover:bg-foreground/90"
                            >
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </CardHeader>
                  {transcript.error_message && (
                    <CardContent className="pt-0">
                      <p className="text-xs text-muted-foreground">
                        Error: {transcript.error_message}
                      </p>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Use Cases — Kanban Board */}
        <TabsContent value="use-cases" className="mt-6">
          <KanbanBoard
            useCases={useCases}
            onCardClick={handleCardClick}
            onRefresh={fetchData}
          />
        </TabsContent>
      </Tabs>

      {/* Use Case Detail Dialog */}
      <UseCaseDetailDialog
        useCase={selectedUseCase}
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) setSelectedUseCase(null);
        }}
        onStatusChange={handleStatusChange}
        onDelete={handleDeleteUseCase}
        onUpdate={fetchData}
      />
    </div>
  );
}