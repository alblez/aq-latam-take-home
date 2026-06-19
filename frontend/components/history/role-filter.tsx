"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type JobFilterProps = Readonly<{
  jobTitles: string[];
  selected: string;
  onChange: (value: string) => void;
}>;

/** @deprecated Renamed export kept for compatibility — use JobFilter */
export const RoleFilter = JobFilter;

export function JobFilter({ jobTitles, selected, onChange }: JobFilterProps) {
  return (
    <Select value={selected} onValueChange={onChange}>
      <SelectTrigger size="sm" className="min-w-[140px]">
        <SelectValue placeholder="All job titles" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="__all__">All job titles</SelectItem>
        {jobTitles.map((title) => (
          <SelectItem key={title} value={title}>
            {title}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
