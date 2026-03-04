import { cn } from "@/lib/utils";

interface TabsProps {
  tabs: { key: string; label: string; count?: number }[];
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function Tabs({ tabs, activeTab, onTabChange }: TabsProps) {
  return (
    <div className="border-b border-gray-800">
      <nav className="flex gap-0 -mb-px overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onTabChange(tab.key)}
            className={cn(
              "whitespace-nowrap border-b-2 px-5 py-3 text-sm font-medium transition-colors",
              activeTab === tab.key
                ? "border-brand-400 text-brand-400"
                : "border-transparent text-gray-400 hover:border-gray-600 hover:text-gray-200"
            )}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={cn(
                  "ml-2 rounded-full px-2 py-0.5 text-xs",
                  activeTab === tab.key
                    ? "bg-brand-400/20 text-brand-400"
                    : "bg-gray-800 text-gray-500"
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </nav>
    </div>
  );
}
