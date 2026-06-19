"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type EarlyEndDialogProps = Readonly<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
  uncoveredCompetencies: string[];
  onConfirm: () => void;
}>;

export function EarlyEndDialog({
  open,
  onOpenChange,
  uncoveredCompetencies,
  onConfirm,
}: EarlyEndDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>End interview early?</DialogTitle>
          <DialogDescription>
            The following competencies haven&apos;t been fully assessed:
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-md bg-warning-muted p-4">
          <ul className="list-disc space-y-1 pl-5 text-sm text-foreground">
            {uncoveredCompetencies.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        </div>

        <p className="text-sm text-foreground-muted">
          This action cannot be undone. Ending now will finalize your session with incomplete
          coverage.
        </p>

        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Continue Interview
          </Button>
          <Button variant="destructive" onClick={onConfirm}>
            End Now
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
