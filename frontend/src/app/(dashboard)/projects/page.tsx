import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Projects</h1>
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">No projects yet</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Your projects will appear here once the projects module is built.
        </CardContent>
      </Card>
    </div>
  );
}
