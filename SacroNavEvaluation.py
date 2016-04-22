import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np


#
# SacroNavEvaluation
#

class SacroNavEvaluation(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SacroNavEvaluation" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# SacroNavEvaluationWidget
#

class SacroNavEvaluationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)



    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply Evaluation")
    self.applyButton.toolTip = "Run the algorithm."
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    
    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    pass

  def onApplyButton(self):
    logic = SacroNavEvaluationLogic()
    logic.run()

#
# SacroNavEvaluationLogic
#

class SacroNavEvaluationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """


  def run(self):
    """
    Run the actual algorithm
    """
    #Obtengo puntos de referencia
    f = slicer.util.getNode('reference_sacro_points')
    sacroToReference = slicer.util.getNode('sacroToReference')

    p1 = [0.0,0.0,0.0]
    p2 = [0.0,0.0,0.0]
    p3 = [0.0,0.0,0.0]

    f.GetNthFiducialPosition(0,p1)
    f.GetNthFiducialPosition(1,p2)
    f.GetNthFiducialPosition(2,p3)

    p1 = p1 + [1.0]
    p2 = p2 + [1.0]
    p3 = p3 + [1.0]

    # transformamos los puntos a sus coordenadas transformadas

    tr= vtk.vtkMatrix4x4()
    sacroToReference.GetMatrixTransformToWorld(tr) 

    p1Transformed = [0.0,0.0,0.0,1.0]
    p2Transformed = [0.0,0.0,0.0,1.0]
    p3Transformed = [0.0,0.0,0.0,1.0]

    tr.MultiplyPoint(p1, p1Transformed)
    tr.MultiplyPoint(p2, p2Transformed)
    tr.MultiplyPoint(p3, p3Transformed)

    p1Transformed =  [p1Transformed[i] for i in (0,1,2)]
    p2Transformed =  [p2Transformed[i] for i in (0,1,2)]
    p3Transformed =  [p3Transformed[i] for i in (0,1,2)]

    m = [np.divide((p1Transformed[0]+p2Transformed[0]+p3Transformed[0]),3),np.divide((p1Transformed[1]+p2Transformed[1]+p3Transformed[1]),3),np.divide((p1Transformed[2]+p2Transformed[2]+p3Transformed[2]),3)]
    #normal
    normal = np.cross(np.subtract(p1,p2),np.subtract(p1,p3))

    fids_original = slicer.vtkMRMLMarkupsFiducialNode()
    fids_original.SetName('Mean Point')
    fids_original.AddFiducialFromArray(m)
    fids_original.GetDisplayNode().SetSelectedColor(0,0,1)
    slicer.mrmlScene.AddNode(fids_original)
    
    plano = self.drawPlane(m, normal)

  def drawPlane(self, m, V_norm):
  

    scene = slicer.mrmlScene
    #create a plane to cut,here it cuts in the XZ direction (xz normal=(1,0,0);XY =(0,0,1),YZ =(0,1,0)
    planex=vtk.vtkPlane()
    planex.SetOrigin(m[0],m[1],m[2])
    planex.SetNormal(V_norm[0],V_norm[1],V_norm[2])
    renderer = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow().GetRenderers().GetFirstRenderer()
    viewSize = renderer.ComputeVisiblePropBounds()
    planexSample = vtk.vtkSampleFunction()
    planexSample.SetImplicitFunction(planex)
    planexSample.SetModelBounds(viewSize)
    planexSample.SetSampleDimensions(50,50,50)
    planexSample.ComputeNormalsOff()
    plane1 = vtk.vtkContourFilter()
    plane1.SetInputConnection(planexSample.GetOutputPort())
    # Create model Plane A node
    planeA = slicer.vtkMRMLModelNode()
    planeA.SetScene(scene)
    planeA.SetName("Symmetry Plane")
    planeA.SetAndObservePolyData(plane1.GetOutput())
    # Create display model Plane A node
    planeAModelDisplay = slicer.vtkMRMLModelDisplayNode()
    planeAModelDisplay.SetColor(0,170,127)
    planeAModelDisplay.BackfaceCullingOff()
    planeAModelDisplay.SetScene(scene)
    scene.AddNode(planeAModelDisplay)
    planeA.SetAndObserveDisplayNodeID(planeAModelDisplay.GetID())
    #Add to scene
    planeAModelDisplay.SetInputPolyDataConnection(plane1.GetOutputPort())
    scene.AddNode(planeA)
    # adjust center of 3d view to plane
    layoutManager = slicer.app.layoutManager()
    threeDWidget = layoutManager.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()

    return plane1

  def calculateNeedleVector(self):
    
    needle = slicer.util.getNode('NeedleModel')
    polydataNeedle = needle.GetPolyData()
    center = polydataNeedle.GetCenter()
    center = [center[i] for i in (0,1,2)]
    center = center + [1.0]

    ssr = vtk.vtkMatrix4x4()
    transform= slicer.util.getNode('needleModelToNeedleTip')
    transform.GetMatrixTransformToWorld(ssr)

    centerTransformed = [0.0,0.0,0.0,1.0]
    ssr.MultiplyPoint(center, centerTransformed)
    centerTransformed = [centerTransformed[i] for i in (0,1,2)]

    m = vtk.vtkMatrix4x4()
    nttn = slicer.util.getNode('needleModelToNeedleTip')
    nttn.GetMatrixTransformToWorld(m)
    tipPoint = [0.0,0.0,0.0]
    tipPoint[0] = m.GetElement(0, 3)
    tipPoint[1] = m.GetElement(1, 3)
    tipPoint[2] = m.GetElement(2, 3)

    needleVector = np.subtract(centerTransformed,tipPoint)

    return needleVector


class SacroNavEvaluationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SacroNavEvaluation1()

  def test_SacroNavEvaluation1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = SacroNavEvaluationLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
