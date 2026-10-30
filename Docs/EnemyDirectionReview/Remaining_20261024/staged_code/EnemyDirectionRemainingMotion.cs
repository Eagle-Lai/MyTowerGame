using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    // Editor-only curves for explicitly described anatomical rigs. Existing approved rigs are untouched.
    public static class EnemyDirectionRemainingMotion
    {
        public static bool TryAdd(AnimationClip clip,string action,EnemyDirectionalRigBuilder.Layout layout,Dictionary<string,Sprite> sprites)
        {
            if(layout.anatomy==null || string.IsNullOrEmpty(layout.motionKind))return false;
            float duration=Mathf.Max(.01f,clip.length),h=layout.referenceHeight;
            bool walk=action=="Walk",attack=action=="Attack",death=action=="Death";
            bool insect=layout.motionKind=="hexapod"||layout.motionKind=="scorpion";
            bool fly=layout.motionKind=="flying"||layout.motionKind=="floating";
            bool crawl=layout.motionKind=="crawler",chest=layout.motionKind=="chest",giant=layout.motionKind=="giant";
            float legAngle=insect?8:giant?9:layout.motionKind=="bird"?12:10;
            float lift=insect?.10f:giant?.14f:.18f;
            foreach(var view in layout.views)
            {
                float forward=view.direction=="Up"?1:-1;
                string motion="DirectionVisual/"+view.direction+"/Motion";
                float center=layout.referenceBottom+h*.5f;
                Set(clip,motion,"m_LocalPosition.x",duration,t=>0,true);
                Set(clip,motion,"m_LocalPosition.y",duration,t=>center+(walk?h*(fly?.018f:insect?.002f:.005f)*(1-Mathf.Cos(4*Mathf.PI*t))*.5f:attack?forward*h*.025f*Pulse(t):0),walk);
                Set(clip,motion,"m_LocalPosition.z",duration,t=>0,true);
                Set(clip,motion,"localEulerAnglesRaw.z",duration,t=>death?(chest?12:insect?18:giant?76:65)*Fall(t):walk&&!fly&&!insect?1.2f*Sin(t):0,walk);
                foreach(var p in view.parts)
                {
                    string path=motion+"/"+p.name;
                    bool leg=p.role=="leg",wing=p.role=="wing",tail=p.role=="tail",arm=p.role=="arm",head=p.role=="head",body=p.role=="body",claw=p.role=="claw",segment=p.role=="segment";
                    float side=p.flipX?1:-1;
                    float phase=p.phase*.5f+(insect?(p.name.Contains("Front")?.04f:p.name.Contains("Back")?-.04f:0):0);
                    Set(clip,path,"m_LocalPosition.x",duration,t=>p.x+(crawl&&segment?h*.007f*Sin(t+phase):0),walk);
                    Set(clip,path,"m_LocalPosition.y",duration,t=>p.y-center+(walk?(body||head||tail?h*(fly?.014f:insect?.002f:.004f)*Sin(t-(tail?.16f:head?.08f:0)):0):attack&&head?forward*h*.02f*Pulse(t):0),walk);
                    Set(clip,path,"m_LocalPosition.z",duration,t=>0,true);
                    Set(clip,path,"localEulerAnglesRaw.z",duration,t=>
                    {
                        float a=p.angle;
                        if(walk)
                        {
                            if(leg)a+=side*legAngle*Sin(t+phase);
                            if(tail)a+=(layout.motionKind=="scorpion"?4:8)*Sin(t-.18f);
                            if(wing)a+=side*(fly?9:2)*Sin(t);
                            if(arm)a+=side*(giant?7:3)*Sin(t+phase);
                            if(claw||p.role=="feeler")a+=side*3*Sin(t+phase);
                            if(head&&!chest)a+=.7f*Sin(t-.08f);
                        }
                        else if(attack)
                        {
                            if(arm)a+=(p.name=="ArmR"?-1:1)*(giant?55:10)*Pulse(t);
                            if(claw)a+=side*forward*24*Pulse(t);
                            if(tail)a+=(insect?16:7)*Pulse(t);
                            if(head)a+=(chest?18:5)*Pulse(t);
                            if(leg)a+=side*8*Pulse(t);
                            if(wing)a+=side*(fly?14:8)*Pulse(t);
                        }
                        else if(death)
                        {
                            if(leg)a+=side*(insect?-30:24)*Fall(t);
                            if(arm||wing||claw)a+=side*25*Fall(t);
                            if(tail)a-=20*Fall(t);
                            if(head)a+=12*Fall(t);
                        }
                        else if(tail||p.role=="feeler")a+=2*Sin(t-.15f);
                        return a;
                    },walk||(!attack&&!death));
                    Set(clip,path,"m_LocalScale.x",duration,t=>crawl&&(body||segment)?1+.035f*Sin(t+phase):1,walk);
                    Set(clip,path,"m_LocalScale.y",duration,t=>walk&&leg?1-lift*Mathf.Pow(Mathf.Max(0,Sin(t+phase)),1.5f):death&&leg?1-.25f*Fall(t):crawl&&(body||segment)?1-.025f*Sin(t+phase):1,walk);
                    Set(clip,path,"m_LocalScale.z",duration,t=>1,true);
                    if(wing&&!string.IsNullOrEmpty(p.alternate))
                    {
                        var frames=new ObjectReferenceKeyframe[5];
                        for(int i=0;i<5;i++)frames[i]=new ObjectReferenceKeyframe{time=duration*i/4,value=sprites[!death&&i%2==1?p.alternate:p.sprite]};
                        AnimationUtility.SetObjectReferenceCurve(clip,EditorCurveBinding.PPtrCurve(path+"/Sprite",typeof(SpriteRenderer),"m_Sprite"),frames);
                    }
                }
            }
            var settings=AnimationUtility.GetAnimationClipSettings(clip);settings.stopTime=duration;AnimationUtility.SetAnimationClipSettings(clip,settings);
            return true;
        }
        private static float Sin(float t){return Mathf.Sin(2*Mathf.PI*t);}
        private static float Fall(float t){return Mathf.SmoothStep(0,1,Mathf.InverseLerp(.08f,.72f,t));}
        private static float Pulse(float t){return t<.28f?-.3f*Mathf.SmoothStep(0,1,t/.28f):t<.44f?Mathf.Lerp(-.3f,1,Mathf.SmoothStep(0,1,(t-.28f)/.16f)):Mathf.Lerp(1,0,Mathf.SmoothStep(0,1,(t-.44f)/.5f));}
        private static void Set(AnimationClip clip,string path,string property,float duration,Func<float,float> sample,bool cyclic)
        {
            const int segments=48;const float epsilon=.0005f;
            var keys=new Keyframe[segments+1];
            for(int i=0;i<=segments;i++)
            {
                float t=(float)i/segments,left=cyclic?t-epsilon:Mathf.Max(0,t-epsilon),right=cyclic?t+epsilon:Mathf.Min(1,t+epsilon);
                float tangent=(sample(right)-sample(left))/((right-left)*duration);
                keys[i]=new Keyframe(t*duration,sample(t),tangent,tangent);
            }
            AnimationUtility.SetEditorCurve(clip,EditorCurveBinding.FloatCurve(path,typeof(Transform),property),new AnimationCurve(keys));
        }
    }
}
