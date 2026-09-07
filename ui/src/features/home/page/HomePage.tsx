import { HeroSection } from "../components/HeroSection";
import { FeatureGrid } from "../components/FeatureGrid";

export default function HomePage() {
  return (
    <div className="space-y-20 fade-in py-4">
      <HeroSection />
      <FeatureGrid />
    </div>
  );
}
