import { useStats } from "@/entities/stats";
import { Card, CardContent } from "@/shared/ui/card";

function Tile({ label, value }: { label: string; value: number }) {
  return (
    <Card className="flex-1">
      <CardContent className="py-6 text-center">
        <div className="text-3xl font-semibold">{value}</div>
        <div className="text-sm text-muted-foreground">{label}</div>
      </CardContent>
    </Card>
  );
}

export function StatsPanel({ deckId }: { deckId: number }) {
  const stats = useStats(deckId);
  if (!stats.data) return <p>Loading…</p>;
  return (
    <div className="flex gap-3">
      <Tile label="Due today" value={stats.data.due_today} />
      <Tile label="Total reviews" value={stats.data.total_reviews} />
    </div>
  );
}
