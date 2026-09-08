import { CvBuilder } from "../components/CvBuilder";

export default function ScreenPage() {
  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden px-4 py-3 sm:px-6">
      <CvBuilder />
    </div>
  );
}
