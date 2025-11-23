import ModelViewer from '@/components/ModelViewer';

const MANUAL_DATA = {
  productName: "SANDSBERG Table",
  steps: [
    { 
      stepNumber: 1, 
      title: "The Base",
      // URL for Step 1 model (Just the table top)
      modelUrl: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/main/2.0/ToyCar/glTF-Binary/ToyCar.glb",
      description: "Place the table top upside down." 
    },
    { 
      stepNumber: 2, 
      title: "Add Brackets",
      // URL for Step 2 model (Table top + Brackets)
      // using a slightly different model to show the swap
      modelUrl: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/main/2.0/ToyCar/glTF-Binary/ToyCar.glb", 
      description: "Insert the corner brackets." 
    },
    { 
      stepNumber: 3, 
      title: "Attach Legs",
      // URL for Step 3 model (Full Assembly)
      modelUrl: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/main/2.0/ToyCar/glTF-Binary/ToyCar.glb",
      description: "Screw in the legs." 
    }
  ]
};

export default function AssemblyScene({ currentStep }: { currentStep: number }) {
  // 1. Find the URL for the current step
  // Safe check: if step doesn't exist, fallback to step 1
  const activeStepData = MANUAL_DATA.steps[currentStep - 1] || MANUAL_DATA.steps[0];
  const activeUrl = activeStepData.modelUrl;

  return (
    <div className="w-full h-full bg-zinc-100">
      {/* The 'key' prop is the magic here. 
         When activeUrl changes, React destroys this instance 
         and creates a fresh one, ensuring the new model loads correctly.
      */}
      <ModelViewer 
        key={activeUrl} 
        url={activeUrl}
        
        // Customizing the look based on your preferences
        width="100%"
        height="100%"
        enableMouseParallax={false}
        enableHoverRotation={false}
        defaultZoom={0.5}
        showScreenshotButton={false}
      />
    </div>
  );
}