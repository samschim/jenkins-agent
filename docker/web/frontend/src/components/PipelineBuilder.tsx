import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  VStack,
  HStack,
  IconButton,
  Text,
  useToast,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Checkbox,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useDisclosure,
} from '@chakra-ui/react';
import { FiPlus, FiTrash2, FiCode, FiEye } from 'react-icons/fi';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface Stage {
  id: string;
  name: string;
  type: string;
  commands: string[];
  parallel: boolean;
  conditions: {
    branch?: string;
    environment?: string;
  };
}

export const PipelineBuilder: React.FC = () => {
  const [stages, setStages] = useState<Stage[]>([]);
  const [pipelineCode, setPipelineCode] = useState<string>('');
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  const addStage = () => {
    const newStage: Stage = {
      id: `stage-${Date.now()}`,
      name: `Stage ${stages.length + 1}`,
      type: 'shell',
      commands: [''],
      parallel: false,
      conditions: {},
    };
    setStages([...stages, newStage]);
  };

  const removeStage = (index: number) => {
    const newStages = [...stages];
    newStages.splice(index, 1);
    setStages(newStages);
  };

  const updateStage = (index: number, field: keyof Stage, value: any) => {
    const newStages = [...stages];
    newStages[index] = { ...newStages[index], [field]: value };
    setStages(newStages);
  };

  const addCommand = (stageIndex: number) => {
    const newStages = [...stages];
    newStages[stageIndex].commands.push('');
    setStages(newStages);
  };

  const updateCommand = (stageIndex: number, cmdIndex: number, value: string) => {
    const newStages = [...stages];
    newStages[stageIndex].commands[cmdIndex] = value;
    setStages(newStages);
  };

  const removeCommand = (stageIndex: number, cmdIndex: number) => {
    const newStages = [...stages];
    newStages[stageIndex].commands.splice(cmdIndex, 1);
    setStages(newStages);
  };

  const onDragEnd = (result: any) => {
    if (!result.destination) return;

    const newStages = [...stages];
    const [reorderedStage] = newStages.splice(result.source.index, 1);
    newStages.splice(result.destination.index, 0, reorderedStage);
    setStages(newStages);
  };

  const generatePipeline = () => {
    let code = 'pipeline {\n  agent any\n\n  stages {\n';

    stages.forEach((stage) => {
      code += `    stage('${stage.name}') {\n`;
      if (stage.parallel) {
        code += '      parallel {\n';
        stage.commands.forEach((cmd, i) => {
          code += `        stage('Step ${i + 1}') {\n`;
          code += '          steps {\n';
          code += `            ${stage.type === 'shell' ? 'sh' : stage.type} '${cmd}'\n`;
          code += '          }\n';
          code += '        }\n';
        });
        code += '      }\n';
      } else {
        code += '      steps {\n';
        stage.commands.forEach((cmd) => {
          code += `        ${stage.type === 'shell' ? 'sh' : stage.type} '${cmd}'\n`;
        });
        code += '      }\n';
      }
      code += '    }\n';
    });

    code += '  }\n}\n';
    setPipelineCode(code);
    onOpen();
  };

  return (
    <Box>
      <HStack mb={4} spacing={4}>
        <Button leftIcon={<FiPlus />} onClick={addStage} colorScheme="blue">
          Add Stage
        </Button>
        <Button leftIcon={<FiCode />} onClick={generatePipeline} colorScheme="green">
          Generate Pipeline
        </Button>
      </HStack>

      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="stages">
          {(provided) => (
            <VStack
              spacing={4}
              align="stretch"
              ref={provided.innerRef}
              {...provided.droppableProps}
            >
              {stages.map((stage, index) => (
                <Draggable key={stage.id} draggableId={stage.id} index={index}>
                  {(provided) => (
                    <Box
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      {...provided.dragHandleProps}
                    >
                      <Accordion allowToggle>
                        <AccordionItem>
                          <AccordionButton>
                            <Box flex="1">
                              <Text fontWeight="bold">{stage.name}</Text>
                            </Box>
                            <AccordionIcon />
                          </AccordionButton>
                          <AccordionPanel>
                            <VStack spacing={4} align="stretch">
                              <FormControl>
                                <FormLabel>Stage Name</FormLabel>
                                <Input
                                  value={stage.name}
                                  onChange={(e) =>
                                    updateStage(index, 'name', e.target.value)
                                  }
                                />
                              </FormControl>

                              <FormControl>
                                <FormLabel>Type</FormLabel>
                                <Select
                                  value={stage.type}
                                  onChange={(e) =>
                                    updateStage(index, 'type', e.target.value)
                                  }
                                >
                                  <option value="shell">Shell</option>
                                  <option value="bat">Batch</option>
                                  <option value="powershell">PowerShell</option>
                                </Select>
                              </FormControl>

                              <Checkbox
                                isChecked={stage.parallel}
                                onChange={(e) =>
                                  updateStage(index, 'parallel', e.target.checked)
                                }
                              >
                                Run steps in parallel
                              </Checkbox>

                              <Box>
                                <Text mb={2}>Commands</Text>
                                {stage.commands.map((cmd, cmdIndex) => (
                                  <HStack key={cmdIndex} mb={2}>
                                    <Input
                                      value={cmd}
                                      onChange={(e) =>
                                        updateCommand(
                                          index,
                                          cmdIndex,
                                          e.target.value
                                        )
                                      }
                                    />
                                    <IconButton
                                      aria-label="Remove command"
                                      icon={<FiTrash2 />}
                                      onClick={() =>
                                        removeCommand(index, cmdIndex)
                                      }
                                      colorScheme="red"
                                      variant="ghost"
                                    />
                                  </HStack>
                                ))}
                                <Button
                                  size="sm"
                                  leftIcon={<FiPlus />}
                                  onClick={() => addCommand(index)}
                                >
                                  Add Command
                                </Button>
                              </Box>

                              <Button
                                leftIcon={<FiTrash2 />}
                                onClick={() => removeStage(index)}
                                colorScheme="red"
                                variant="ghost"
                              >
                                Remove Stage
                              </Button>
                            </VStack>
                          </AccordionPanel>
                        </AccordionItem>
                      </Accordion>
                    </Box>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </VStack>
          )}
        </Droppable>
      </DragDropContext>

      <Drawer isOpen={isOpen} onClose={onClose} size="lg">
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>Generated Pipeline</DrawerHeader>
          <DrawerBody>
            <Box position="relative">
              <IconButton
                aria-label="Copy code"
                icon={<FiCode />}
                position="absolute"
                top={2}
                right={2}
                onClick={() => {
                  navigator.clipboard.writeText(pipelineCode);
                  toast({
                    title: 'Copied to clipboard',
                    status: 'success',
                    duration: 2000,
                  });
                }}
              />
              <SyntaxHighlighter
                language="groovy"
                style={tomorrow}
                customStyle={{ fontSize: '14px' }}
              >
                {pipelineCode}
              </SyntaxHighlighter>
            </Box>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  );
};