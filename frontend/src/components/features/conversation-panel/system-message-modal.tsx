import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "#/components/ui/dialog";
import { ScrollArea } from "#/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "#/components/ui/tabs";

interface SystemMessageModalProps {
  isOpen: boolean;
  onClose: () => void;
  systemMessage: {
    content: string;
    tools: any[] | null;
    openhands_version: string | null;
    agent_class: string | null;
  } | null;
}

export function SystemMessageModal({
  isOpen,
  onClose,
  systemMessage,
}: SystemMessageModalProps) {
  if (!systemMessage) {
    return null;
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Agent Tools & Metadata</DialogTitle>
          <DialogDescription>
            <div className="flex flex-col gap-1">
              {systemMessage.agent_class && (
                <div className="text-sm text-muted-foreground">
                  Agent Class: {systemMessage.agent_class}
                </div>
              )}
              {systemMessage.openhands_version && (
                <div className="text-sm text-muted-foreground">
                  OpenHands Version: {systemMessage.openhands_version}
                </div>
              )}
            </div>
          </DialogDescription>
        </DialogHeader>
        <Tabs defaultValue="system" className="flex-1 flex flex-col">
          <TabsList>
            <TabsTrigger value="system">System Message</TabsTrigger>
            <TabsTrigger value="tools">Available Tools</TabsTrigger>
          </TabsList>
          <TabsContent value="system" className="flex-1">
            <ScrollArea className="h-[50vh]">
              <div className="p-4 whitespace-pre-wrap font-mono text-sm">
                {systemMessage.content}
              </div>
            </ScrollArea>
          </TabsContent>
          <TabsContent value="tools" className="flex-1">
            <ScrollArea className="h-[50vh]">
              {systemMessage.tools && systemMessage.tools.length > 0 ? (
                <div className="p-4 space-y-4">
                  {systemMessage.tools.map((tool, index) => (
                    <div key={index} className="border rounded-md p-4">
                      <h3 className="font-bold">{tool.name}</h3>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {tool.description}
                      </p>
                      {tool.parameters && (
                        <div className="mt-2">
                          <h4 className="text-sm font-semibold">Parameters:</h4>
                          <pre className="text-xs mt-1 p-2 bg-muted rounded-md overflow-auto">
                            {JSON.stringify(tool.parameters, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-muted-foreground">
                  No tools available
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}