import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, BookOpen, CheckCircle2 } from "lucide-react";

interface LearningResource {
  title: string;
  organization: string;
  url: string;
  rating: string;
  difficulty: string;
  type: string;
  verified: boolean;
}

interface LearningResourceCardProps {
  resource: LearningResource;
}

export function LearningResourceCard({ resource }: LearningResourceCardProps) {
  return (
    <a
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group block"
    >
      <Card className="h-full hover:shadow-md transition-all duration-200 border border-muted hover:border-primary/30">
        <CardContent className="p-4 flex items-start gap-3">
          <div className="mt-1">
            <BookOpen className="h-5 w-5 text-primary/70 group-hover:text-primary transition-colors" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-foreground group-hover:text-primary transition-colors line-clamp-2 leading-tight">
              {resource.title}
            </h4>
            <p className="text-sm text-muted-foreground mt-1 truncate">
              {resource.organization}
            </p>
          </div>
          <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </CardContent>
      </Card>
    </a>
  );
}

interface SkillGapWithResourcesProps {
  skillName: string;
  importance: 'critical' | 'important' | 'nice-to-have';
  learningResources: string[];
}

export function SkillGapWithResources({
  skillName,
  importance,
  learningResources
}: SkillGapWithResourcesProps) {
  const parseResource = (resourceStr: string): LearningResource | null => {
    // Format: "Title - Organization (URL)"
    const match = resourceStr.match(/^(.+?)\s*-\s*(.+?)\s*\((.+?)\)$/);
    if (!match) return null;

    return {
      title: match[1].trim(),
      organization: match[2].trim(),
      url: match[3].trim(),
      rating: "0",
      difficulty: "Unknown",
      type: "Course",
      verified: true
    };
  };

  const getImportanceColor = () => {
    switch (importance) {
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'important':
        return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'nice-to-have':
        return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const resources = learningResources
    .map(parseResource)
    .filter((r): r is LearningResource => r !== null);

  if (resources.length === 0) return null;

  return (
    <div className="space-y-3 pt-2">
      <div className="flex items-center gap-3">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          {skillName}
        </h3>
        <Badge variant="outline" className={`${getImportanceColor()} border`}>
          {importance.charAt(0).toUpperCase() + importance.slice(1).replace(/-/g, ' ')}
        </Badge>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {resources.map((resource, idx) => (
          <LearningResourceCard key={idx} resource={resource} />
        ))}
      </div>
    </div>
  );
}
