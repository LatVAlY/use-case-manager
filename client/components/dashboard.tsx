"use client";

import { useEffect, useState, useCallback } from "react";
import {
  listIndustries,
  createIndustry,
  deleteIndustry,
  listCompanies,
  createCompany,
  deleteCompany,
  type IndustryResponse,
  type CompanyResponse,
} from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Plus,
  Trash2,
  ArrowRight,
  Building2,
  Factory,
  Globe,
} from "lucide-react";
import Link from "next/link";

export function Dashboard() {
  const [industries, setIndustries] = useState<IndustryResponse[]>([]);
  const [companies, setCompanies] = useState<CompanyResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Industry form
  const [industryOpen, setIndustryOpen] = useState(false);
  const [indName, setIndName] = useState("");
  const [indDesc, setIndDesc] = useState("");
  const [creatingInd, setCreatingInd] = useState(false);

  // Company form
  const [companyOpen, setCompanyOpen] = useState(false);
  const [compName, setCompName] = useState("");
  const [compDesc, setCompDesc] = useState("");
  const [compWebsite, setCompWebsite] = useState("");
  const [compIndustryId, setCompIndustryId] = useState("");
  const [creatingComp, setCreatingComp] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [indRes, compRes] = await Promise.all([
        listIndustries(),
        listCompanies(),
      ]);
      setIndustries(indRes.items || []);
      setCompanies(compRes.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleCreateIndustry(e: React.FormEvent) {
    e.preventDefault();
    setCreatingInd(true);
    try {
      await createIndustry({ name: indName, description: indDesc || undefined });
      setIndName("");
      setIndDesc("");
      setIndustryOpen(false);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create industry");
    } finally {
      setCreatingInd(false);
    }
  }

  async function handleDeleteIndustry(id: string) {
    try {
      await deleteIndustry(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete industry");
    }
  }

  async function handleCreateCompany(e: React.FormEvent) {
    e.preventDefault();
    setCreatingComp(true);
    try {
      await createCompany({
        name: compName,
        industry_id: compIndustryId,
        description: compDesc || undefined,
        website: compWebsite || undefined,
      });
      setCompName("");
      setCompDesc("");
      setCompWebsite("");
      setCompIndustryId("");
      setCompanyOpen(false);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create company");
    } finally {
      setCreatingComp(false);
    }
  }

  async function handleDeleteCompany(id: string) {
    try {
      await deleteCompany(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete company");
    }
  }

  function getIndustryName(industryId: string) {
    return industries.find((i) => i.id === industryId)?.name || "Unknown";
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-md border border-foreground/20 bg-foreground/5 px-4 py-3 text-sm text-foreground">
          {error}
          <button onClick={() => setError("")} className="ml-2 underline">
            dismiss
          </button>
        </div>
      )}

      <Tabs defaultValue="companies" className="w-full">
        <TabsList className="w-full justify-start bg-foreground/5">
          <TabsTrigger value="companies" className="gap-2">
            <Building2 className="h-4 w-4" />
            Companies
            <Badge variant="secondary" className="ml-1">
              {companies.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="industries" className="gap-2">
            <Factory className="h-4 w-4" />
            Industries
            <Badge variant="secondary" className="ml-1">
              {industries.length}
            </Badge>
          </TabsTrigger>
        </TabsList>

        {/* Companies Tab */}
        <TabsContent value="companies" className="mt-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">Companies</h2>
              <p className="text-sm text-muted-foreground">
                Manage companies, upload transcripts, and extract use cases
              </p>
            </div>
            <Dialog open={companyOpen} onOpenChange={setCompanyOpen}>
              <DialogTrigger asChild>
                <Button disabled={industries.length === 0}>
                  <Plus className="mr-2 h-4 w-4" />
                  New Company
                </Button>
              </DialogTrigger>
              <DialogContent className="border-foreground/10">
                <form onSubmit={handleCreateCompany}>
                  <DialogHeader>
                    <DialogTitle>Create Company</DialogTitle>
                    <DialogDescription>
                      Add a new company to start uploading transcripts.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="comp-name">Name</Label>
                      <Input
                        id="comp-name"
                        placeholder="Company name"
                        value={compName}
                        onChange={(e) => setCompName(e.target.value)}
                        required
                        className="border-foreground/20"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="comp-industry">Industry</Label>
                      <Select value={compIndustryId} onValueChange={setCompIndustryId} required>
                        <SelectTrigger className="border-foreground/20">
                          <SelectValue placeholder="Select industry" />
                        </SelectTrigger>
                        <SelectContent>
                          {industries.map((ind) => (
                            <SelectItem key={ind.id} value={ind.id}>
                              {ind.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="comp-desc">Description (optional)</Label>
                      <Textarea
                        id="comp-desc"
                        placeholder="Brief description"
                        value={compDesc}
                        onChange={(e) => setCompDesc(e.target.value)}
                        className="border-foreground/20"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="comp-website">Website (optional)</Label>
                      <Input
                        id="comp-website"
                        type="url"
                        placeholder="https://example.com"
                        value={compWebsite}
                        onChange={(e) => setCompWebsite(e.target.value)}
                        className="border-foreground/20"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setCompanyOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={creatingComp || !compIndustryId}>
                      {creatingComp ? <Spinner className="mr-2" /> : null}
                      Create
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {industries.length === 0 && (
            <div className="rounded-md border border-foreground/20 bg-foreground/5 px-4 py-3 text-sm text-foreground">
              Create an industry first before adding companies.
            </div>
          )}

          {companies.length === 0 ? (
            <Card className="border-dashed border-foreground/10">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Building2 className="mb-4 h-12 w-12 text-muted-foreground/50" />
                <h3 className="mb-1 text-lg font-medium">No companies yet</h3>
                <p className="mb-4 text-sm text-muted-foreground">
                  Add your first company to get started
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {companies.map((company) => (
                <Card
                  key={company.id}
                  className="group relative border-foreground/10 transition-colors hover:border-foreground/20"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg leading-tight">
                        {company.name}
                      </CardTitle>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-muted-foreground opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Delete company</span>
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent className="border-foreground/10">
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete company?</AlertDialogTitle>
                            <AlertDialogDescription>
                              This will permanently delete the company and all associated data.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteCompany(company.id)}
                              className="bg-foreground text-background hover:bg-foreground/90"
                            >
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                    <CardDescription className="line-clamp-2">
                      {company.description || "No description"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="border-foreground/20 text-xs">
                          <Factory className="mr-1 h-3 w-3" />
                          {getIndustryName(company.industry_id)}
                        </Badge>
                        {company.website && (
                          <Badge variant="outline" className="border-foreground/20 text-xs">
                            <Globe className="mr-1 h-3 w-3" />
                            Website
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center justify-between pt-2">
                        <span className="text-xs text-muted-foreground">
                          Created {new Date(company.created_at).toLocaleDateString()}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          asChild
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <Link href={`/dashboard/companies/${company.id}`}>
                            Open
                            <ArrowRight className="ml-1 h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Industries Tab */}
        <TabsContent value="industries" className="mt-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">Industries</h2>
              <p className="text-sm text-muted-foreground">
                Manage industry categories for your companies
              </p>
            </div>
            <Dialog open={industryOpen} onOpenChange={setIndustryOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Industry
                </Button>
              </DialogTrigger>
              <DialogContent className="border-foreground/10">
                <form onSubmit={handleCreateIndustry}>
                  <DialogHeader>
                    <DialogTitle>Create Industry</DialogTitle>
                    <DialogDescription>
                      Add a new industry category.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="ind-name">Name</Label>
                      <Input
                        id="ind-name"
                        placeholder="Industry name"
                        value={indName}
                        onChange={(e) => setIndName(e.target.value)}
                        required
                        className="border-foreground/20"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="ind-desc">Description (optional)</Label>
                      <Textarea
                        id="ind-desc"
                        placeholder="Brief description"
                        value={indDesc}
                        onChange={(e) => setIndDesc(e.target.value)}
                        className="border-foreground/20"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setIndustryOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={creatingInd}>
                      {creatingInd ? <Spinner className="mr-2" /> : null}
                      Create
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {industries.length === 0 ? (
            <Card className="border-dashed border-foreground/10">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Factory className="mb-4 h-12 w-12 text-muted-foreground/50" />
                <h3 className="mb-1 text-lg font-medium">No industries yet</h3>
                <p className="mb-4 text-sm text-muted-foreground">
                  Create your first industry to categorize companies
                </p>
                <Button onClick={() => setIndustryOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  New Industry
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {industries.map((industry) => {
                const compCount = companies.filter((c) => c.industry_id === industry.id).length;
                return (
                  <Card
                    key={industry.id}
                    className="group relative border-foreground/10 transition-colors hover:border-foreground/20"
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-lg leading-tight">
                          {industry.name}
                        </CardTitle>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0 text-muted-foreground opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
                            >
                              <Trash2 className="h-4 w-4" />
                              <span className="sr-only">Delete industry</span>
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent className="border-foreground/10">
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete industry?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This will permanently delete the industry. Make sure no companies are using it.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDeleteIndustry(industry.id)}
                                className="bg-foreground text-background hover:bg-foreground/90"
                              >
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                      {industry.description && (
                        <CardDescription className="line-clamp-2">
                          {industry.description}
                        </CardDescription>
                      )}
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <Badge variant="secondary" className="text-xs">
                          {compCount} {compCount === 1 ? "company" : "companies"}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          Created {new Date(industry.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
