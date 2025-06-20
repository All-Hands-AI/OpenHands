import React from "react";
import {
  Github,
  GitBranch,
  Plus,
  Settings,
  User,
  Bell,
  Search,
  MessageSquare,
  FileText,
  Code,
  Terminal,
  Globe,
  AlertCircle,
  CheckCircle,
  Info,
  X,
  ChevronDown,
  ChevronRight,
  ArrowRight,
  Download,
  Upload,
  Trash2,
  Edit,
  Copy,
  ExternalLink,
  Menu,
  Home,
  Folder,
  Calendar,
  Clock,
  Tag,
  Filter,
  Grid,
  List,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Wifi,
  WifiOff,
  Battery,
  Volume2,
  VolumeX,
  Sun,
  Moon,
  Monitor,
  Smartphone,
  Tablet
} from "lucide-react";

// Import actual components
import { BrandButton } from "#/components/features/settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { CustomInput } from "#/components/shared/custom-input";
import { WavingHand } from "#/components/shared/icons/waving-hand";

interface ComponentSectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
}

function ComponentSection({ title, description, children }: ComponentSectionProps) {
  return (
    <section className="mb-12">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-content mb-2">{title}</h2>
        {description && (
          <p className="text-sm text-content-secondary">{description}</p>
        )}
      </div>
      <div className="bg-base-secondary rounded-xl p-6 border border-border">
        {children}
      </div>
    </section>
  );
}

interface ComponentExampleProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

function ComponentExample({ title, children, className = "" }: ComponentExampleProps) {
  return (
    <div className={`mb-6 ${className}`}>
      <h3 className="text-sm font-medium text-content mb-3">{title}</h3>
      <div className="flex flex-wrap gap-4 items-center">
        {children}
      </div>
    </div>
  );
}

function ComponentsShowcase() {
  return (
    <div className="min-h-screen bg-base p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="mb-12 text-center">
          <h1 className="heading mb-4">UI Components Showcase</h1>
          <p className="text-sm text-content-secondary max-w-2xl mx-auto">
            A comprehensive display of all UI components used throughout the OpenHands application.
            Each component is shown with various states and configurations.
          </p>
        </header>

        {/* Typography & Text Styles */}
        <ComponentSection
          title="Typography & Text Styles"
          description="All text styles and typography used in the application"
        >
          <ComponentExample title="Headings">
            <h1 className="heading">Heading 1 - Main Title</h1>
            <h2 className="text-xl font-semibold text-content">Heading 2 - Section Title</h2>
            <h3 className="text-lg font-medium text-content">Heading 3 - Subsection</h3>
            <h4 className="text-base font-medium text-content">Heading 4 - Card Title</h4>
          </ComponentExample>

          <ComponentExample title="Body Text">
            <p className="text-sm text-content">Regular body text (text-sm text-content)</p>
            <p className="text-sm text-content-secondary">Secondary text (text-sm text-content-secondary)</p>
            <p className="text-sm text-gray-400">Muted text (text-sm text-gray-400)</p>
            <p className="text-sm text-white">White text (text-sm text-white)</p>
          </ComponentExample>

          <ComponentExample title="Special Text Styles">
            <span className="text-sm font-medium text-content">Medium weight</span>
            <span className="text-sm font-semibold text-content">Semibold weight</span>
            <span className="text-sm font-bold text-content">Bold weight</span>
            <span className="text-sm italic text-content">Italic text</span>
            <span className="text-sm underline text-content">Underlined text</span>
          </ComponentExample>
        </ComponentSection>

        {/* Colors */}
        <ComponentSection
          title="Color Palette"
          description="All colors defined in the design system"
        >
          <ComponentExample title="Primary Colors">
            <div className="flex gap-4">
              <div className="text-center">
                <div className="w-16 h-16 bg-primary rounded-lg mb-2"></div>
                <span className="text-xs text-content">Primary<br/>#C9B974</span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-logo rounded-lg mb-2"></div>
                <span className="text-xs text-content">Logo<br/>#CFB755</span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-base rounded-lg mb-2 border border-border"></div>
                <span className="text-xs text-content">Base<br/>#0D0F11</span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-base-secondary rounded-lg mb-2"></div>
                <span className="text-xs text-content">Base Secondary<br/>#24272E</span>
              </div>
            </div>
          </ComponentExample>

          <ComponentExample title="Semantic Colors">
            <div className="flex gap-4">
              <div className="text-center">
                <div className="w-16 h-16 bg-danger rounded-lg mb-2"></div>
                <span className="text-xs text-content">Danger<br/>#E76A5E</span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-success rounded-lg mb-2"></div>
                <span className="text-xs text-content">Success<br/>#A5E75E</span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-basic rounded-lg mb-2"></div>
                <span className="text-xs text-content">Basic<br/>#9099AC</span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-tertiary rounded-lg mb-2"></div>
                <span className="text-xs text-content">Tertiary<br/>#454545</span>
              </div>
            </div>
          </ComponentExample>

          <ComponentExample title="Text Colors">
            <div className="flex gap-4">
              <div className="text-center">
                <div className="w-16 h-16 bg-content rounded-lg mb-2"></div>
                <span className="text-xs text-content">Content<br/>#ECEDEE</span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-content-2 rounded-lg mb-2"></div>
                <span className="text-xs text-content">Content 2<br/>#F9FBFE</span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-tertiary-light rounded-lg mb-2"></div>
                <span className="text-xs text-content">Tertiary Light<br/>#B7BDC2</span>
              </div>
            </div>
          </ComponentExample>
        </ComponentSection>

        {/* Buttons */}
        <ComponentSection
          title="Button Styles"
          description="All button variants and states used in the application"
        >
          <ComponentExample title="Buttons">
            <button className="px-4 py-2 text-sm rounded bg-black text-white hover:bg-gray-800 transition-colors">
              Primary Button
            </button>
            <button className="px-4 py-2 text-sm rounded bg-white text-black border border-border hover:bg-gray-100 transition-colors">
              Secondary Button
            </button>
            <button className="px-4 py-2 text-sm rounded bg-transparent text-black border border-black hover:bg-black hover:text-white transition-colors">
              Outline Button
            </button>
          </ComponentExample>

          <ComponentExample title="GitHub & GitLab Buttons">
            <button className="flex items-center gap-1.5 px-3 py-2 text-sm rounded disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition-colors duration-150 bg-[#24292e] text-white hover:bg-[#1b1f23]">
              <Github className="w-4 h-4" />
              Connect GitHub
            </button>
            <button className="flex items-center gap-1.5 px-3 py-2 text-sm rounded disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition-colors duration-150 bg-[#fc6d26] text-white hover:bg-[#e24329]">
              <GitBranch className="w-4 h-4" />
              Connect GitLab
            </button>
          </ComponentExample>

          <ComponentExample title="Icon Buttons">
            <button className="p-2 text-sm rounded disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition-colors duration-150 bg-white text-black hover:bg-gray-100">
              <Settings className="w-4 h-4" />
            </button>
            <button className="p-2 text-sm rounded disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition-colors duration-150 bg-white text-black hover:bg-gray-100">
              <User className="w-4 h-4" />
            </button>
            <button className="p-2 text-sm rounded disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition-colors duration-150 bg-white text-black hover:bg-gray-100">
              <Bell className="w-4 h-4" />
            </button>
          </ComponentExample>

          <ComponentExample title="Button Sizes">
            <button className="px-6 py-2 text-sm rounded bg-white text-black hover:bg-gray-100">Large</button>
            <button className="px-3 py-2 text-sm rounded bg-white text-black hover:bg-gray-100">Medium</button>
            <button className="px-2 py-1 text-xs rounded bg-white text-black hover:bg-gray-100">Small</button>
          </ComponentExample>
        </ComponentSection>

        {/* Form Elements */}
        <ComponentSection
          title="Form Elements"
          description="Input fields, selects, and other form components"
        >
          <ComponentExample title="Text Inputs">
            <CustomInput name="example" label="Example Input" />
            <CustomInput name="disabled" label="Disabled Input" defaultValue="Disabled" />
            <input
              type="text"
              placeholder="Regular input"
              className="bg-transparent border border-border rounded-md px-3 py-2 text-sm text-content-secondary focus:outline-none focus:text-white focus:border-white focus:ring-1 focus:ring-white"
            />
          </ComponentExample>

          <ComponentExample title="Select Dropdowns">
            <select className="bg-transparent border border-border rounded-md px-3 py-2 text-sm text-content-secondary focus:outline-none focus:text-white focus:border-white focus:ring-1 focus:ring-white">
              <option>Select an option</option>
              <option>Option 1</option>
              <option>Option 2</option>
              <option>Option 3</option>
            </select>
          </ComponentExample>

          <ComponentExample title="Chat Input Field">
            <div className="w-full max-w-md">
              <div className="flex items-end justify-end grow gap-1 min-h-6 w-full">
                <textarea
                  placeholder="Type your message..."
                  className="grow text-sm self-center placeholder:text-neutral-400 text-white resize-none outline-none ring-0 bg-transparent border border-border rounded-md px-3 py-2"
                  rows={1}
                />
                <button className="p-2 text-sm rounded bg-white text-black hover:bg-gray-100">
                  Send
                </button>
              </div>
            </div>
          </ComponentExample>
        </ComponentSection>

        {/* Icons */}
        <ComponentSection
          title="Icons"
          description="All icons used throughout the application"
        >
          <ComponentExample title="Navigation Icons">
            <Home className="w-6 h-6 text-content" />
            <Settings className="w-6 h-6 text-content" />
            <User className="w-6 h-6 text-content" />
            <Bell className="w-6 h-6 text-content" />
            <Search className="w-6 h-6 text-content" />
            <MessageSquare className="w-6 h-6 text-content" />
            <FileText className="w-6 h-6 text-content" />
            <Code className="w-6 h-6 text-content" />
            <Terminal className="w-6 h-6 text-content" />
            <Globe className="w-6 h-6 text-content" />
          </ComponentExample>

          <ComponentExample title="Action Icons">
            <Plus className="w-6 h-6 text-content" />
            <Edit className="w-6 h-6 text-content" />
            <Copy className="w-6 h-6 text-content" />
            <Trash2 className="w-6 h-6 text-content" />
            <Download className="w-6 h-6 text-content" />
            <Upload className="w-6 h-6 text-content" />
            <ExternalLink className="w-6 h-6 text-content" />
            <Menu className="w-6 h-6 text-content" />
          </ComponentExample>

          <ComponentExample title="Status Icons">
            <CheckCircle className="w-6 h-6 text-success" />
            <AlertCircle className="w-6 h-6 text-danger" />
            <Info className="w-6 h-6 text-primary" />
            <X className="w-6 h-6 text-content" />
            <ChevronDown className="w-6 h-6 text-content" />
            <ChevronRight className="w-6 h-6 text-content" />
            <ArrowRight className="w-6 h-6 text-content" />
          </ComponentExample>

          <ComponentExample title="Custom Icons">
            <div className="w-6 h-6">
              <WavingHand />
            </div>
          </ComponentExample>
        </ComponentSection>

        {/* Loading States */}
        <ComponentSection
          title="Loading States"
          description="Loading spinners, skeletons, and other loading indicators"
        >
          <ComponentExample title="Loading Spinner">
            <LoadingSpinner size="small" />
            <LoadingSpinner size="large" />
          </ComponentExample>

          <ComponentExample title="Skeleton Loading">
            <div className="skeleton w-32 h-8 mb-2"></div>
            <div className="skeleton w-48 h-4 mb-2"></div>
            <div className="skeleton w-24 h-4"></div>
          </ComponentExample>

          <ComponentExample title="Typing Indicator">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </ComponentExample>

          <ComponentExample title="Success/Error Indicators">
            <CheckCircle className="w-6 h-6 text-success" />
            <AlertCircle className="w-6 h-6 text-danger" />
            <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center">
              <Clock className="w-4 h-4 text-black" />
            </div>
          </ComponentExample>
        </ComponentSection>

        {/* Notifications & Tooltips */}
        <ComponentSection
          title="Notifications & Tooltips"
          description="Toast notifications, tooltips, and alert messages"
        >
          <ComponentExample title="Alert Messages">
            <div className="bg-danger/20 border border-danger/30 rounded-lg p-3 text-sm text-danger">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                <span>Error: Something went wrong</span>
              </div>
            </div>
            <div className="bg-success/20 border border-success/30 rounded-lg p-3 text-sm text-success">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                <span>Success: Operation completed</span>
              </div>
            </div>
            <div className="bg-primary/20 border border-primary/30 rounded-lg p-3 text-sm text-primary">
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4" />
                <span>Info: Here's some information</span>
              </div>
            </div>
          </ComponentExample>

          <ComponentExample title="Tooltip Example">
            <div className="relative group">
              <button className="p-2 text-sm rounded bg-white text-black hover:bg-gray-100">
                <Info className="w-4 h-4" />
              </button>
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-base text-content text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity">
                This is a tooltip
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-base"></div>
              </div>
            </div>
          </ComponentExample>
        </ComponentSection>

        {/* Chat Components */}
        <ComponentSection
          title="Chat Components"
          description="All components used in the chat interface"
        >
          <ComponentExample title="Chat Interface Elements">
            <div className="w-full max-w-md space-y-4">
              <div className="bg-base-secondary rounded-lg p-3">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-black" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-content">This is a user message in the chat interface.</p>
                    <p className="text-xs text-content-secondary mt-1">Just now</p>
                  </div>
                </div>
              </div>

              <div className="bg-primary/20 rounded-lg p-3">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                    <Code className="w-4 h-4 text-black" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-content">This is an AI assistant message with a different background.</p>
                    <p className="text-xs text-content-secondary mt-1">Just now</p>
                  </div>
                </div>
              </div>
            </div>
          </ComponentExample>

          <ComponentExample title="Browser Component">
            <div className="w-full max-w-md h-32 bg-base-secondary rounded-lg p-3 border border-border">
              <div className="w-full p-2 truncate border-b border-border text-sm text-neutral-400">
                https://example.com
              </div>
              <div className="flex items-center justify-center h-full text-sm text-neutral-400">
                Browser component placeholder
              </div>
            </div>
          </ComponentExample>
        </ComponentSection>

        {/* Layout Components */}
        <ComponentSection
          title="Layout Components"
          description="Cards, containers, and layout elements"
        >
          <ComponentExample title="Cards">
            <div className="border border-border rounded-xl p-6 w-64">
              <div className="flex items-center gap-3 mb-4">
                <GitBranch className="w-6 h-6 text-content" />
                <h2 className="text-xl leading-6 font-semibold text-content">Card Title</h2>
              </div>
              <p className="text-sm text-content-secondary mb-4">
                This is a card component with a border, padding, and rounded corners.
              </p>
              <button className="w-fit p-2 text-sm rounded bg-white text-black hover:bg-gray-100">
                Action Button
              </button>
            </div>
          </ComponentExample>

          <ComponentExample title="Containers">
            <div className="bg-base-secondary rounded-xl p-6 w-64">
              <h3 className="text-lg font-medium text-content mb-2">Secondary Container</h3>
              <p className="text-sm text-content-secondary">
                This container uses the base-secondary background color.
              </p>
            </div>
          </ComponentExample>

          <ComponentExample title="Dividers">
            <div className="w-64">
              <p className="text-sm text-content mb-2">Content above</p>
              <hr className="border-border my-2" />
              <p className="text-sm text-content">Content below</p>
            </div>
          </ComponentExample>
        </ComponentSection>

        {/* Interactive Elements */}
        <ComponentSection
          title="Interactive Elements"
          description="Hover states, focus states, and interactive components"
        >
          <ComponentExample title="Hover States">
            <button className="px-3 py-2 text-sm rounded bg-black text-white hover:bg-gray-800 transition-colors">
              Primary hover
            </button>
            <button className="px-3 py-2 text-sm rounded bg-white text-black border border-border hover:bg-gray-100 transition-colors">
              Secondary hover
            </button>
            <button className="px-3 py-2 text-sm rounded bg-transparent text-black border border-black hover:bg-black hover:text-white transition-colors">
              Border hover
            </button>
          </ComponentExample>

          <ComponentExample title="Focus States">
            <input
              type="text"
              placeholder="Focus me"
              className="bg-transparent border border-border rounded-md px-3 py-2 text-sm text-content-secondary focus:outline-none focus:text-white focus:border-white focus:ring-1 focus:ring-white"
            />
          </ComponentExample>

          <ComponentExample title="Disabled States">
            <button className="px-3 py-2 text-sm rounded bg-white text-black opacity-30 cursor-not-allowed">
              Disabled Button
            </button>
            <input
              type="text"
              placeholder="Disabled input"
              disabled
              className="bg-transparent border border-border rounded-md px-3 py-2 text-sm text-content-secondary opacity-30 cursor-not-allowed"
            />
          </ComponentExample>
        </ComponentSection>

        {/* Animations */}
        <ComponentSection
          title="Animations"
          description="CSS animations and transitions used in the application"
        >
          <ComponentExample title="Wave Animation">
            <div className="w-16 h-16">
              <WavingHand />
            </div>
          </ComponentExample>

          <ComponentExample title="Pulse Animation">
            <div className="skeleton w-16 h-16 rounded-full"></div>
          </ComponentExample>

          <ComponentExample title="Transition Effects">
            <button className="px-3 py-2 text-sm rounded bg-white text-black hover:bg-gray-100 transition-all duration-150 hover:scale-105">
              Scale on hover
            </button>
            <button className="px-3 py-2 text-sm rounded bg-white text-black hover:bg-gray-100 transition-colors duration-150">
              Color transition
            </button>
          </ComponentExample>
        </ComponentSection>
      </div>
    </div>
  );
}

export default ComponentsShowcase;
