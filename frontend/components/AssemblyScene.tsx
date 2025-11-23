import React, { Suspense, useMemo, useEffect } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
// 1. Add Environment to imports
import { OrbitControls, Stage, useGLTF, Html, useProgress, Environment } from '@react-three/drei';

// --- 1. LOADER COMPONENT ---
function Loader() {
  const { progress } = useProgress();
  return (
    <Html center>
      <div className="flex flex-col items-center whitespace-nowrap">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-2"></div>
        <span className="text-white font-mono text-sm">{Math.round(progress)}% loaded</span>
      </div>
    </Html>
  );
}

// --- 2. THE MODEL COMPONENT ---
interface ModelProps {
  url: string;
}

function Model({ url }: ModelProps) {
  const { scene } = useGLTF(url);
  const clonedScene = useMemo(() => scene.clone(), [scene]);
  return <primitive object={clonedScene} />;
}

// --- 3. CAMERA HANDLER ---
interface CameraHandlerProps {
  url: string;
}

function CameraHandler({ url }: CameraHandlerProps) {
  const { camera, controls } = useThree();
  useEffect(() => {
    // Reset camera position to isometric view when model changes
    camera.position.set(8, 8, 8);
    camera.lookAt(0, 0, 0);

    // Reset controls target if OrbitControls are being used
    if (controls) {
      (controls as any).target.set(0, 0, 0);
      (controls as any).update();
    }
  }, [url, camera, controls]);
  return null;
}

// --- 4. MAIN SCENE ---
interface AssemblySceneProps {
  modelUrl: string;
}

export default function AssemblyScene({ modelUrl }: AssemblySceneProps) {
  return (
    <div className="w-full h-full bg-zinc-900">
      <Canvas shadows dpr={[1, 2]} camera={{ position: [8, 8, 8], fov: 50 }}>

        <Suspense fallback={<Loader />}>
          {/* 2. FIX: Remove 'environment="forest"' from Stage.
            This prevents Stage from triggering the load during its render cycle.
          */}
          <Stage
            intensity={0}
            adjustCamera={true}
          >
            {modelUrl && <Model key={modelUrl} url={modelUrl} />}
          </Stage>

          {/* 3. FIX: Add Environment explicitly as a sibling.
            This allows React to handle the environment loading independently
            of the Stage's internal render logic.
          */}
          <Environment preset="forest" />
        </Suspense>

        <OrbitControls makeDefault />
        <CameraHandler url={modelUrl} />

      </Canvas>
    </div>
  );
}