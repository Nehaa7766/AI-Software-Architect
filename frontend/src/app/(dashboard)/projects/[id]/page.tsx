"use client";

import { useParams } from "next/navigation";

import { ProjectDetailView } from "@/features/projects/components/ProjectDetailView";

export default function ProjectPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : String(params.id);
  return <ProjectDetailView projectId={id} />;
}
