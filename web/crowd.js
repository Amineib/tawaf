/* Instanced, speed-matched walking. No per-person skeletons or animation mixers. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.TourCrowd = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const vertex = `
attribute vec3 _umrah_gait;
attribute vec2 crowdMotion;
uniform float uCrowdTime;
vec2 umrahRotate(vec2 p, float angle) {
  float c = cos(angle), s = sin(angle);
  return vec2(c*p.x-s*p.y, s*p.x+c*p.y);
}
float umrahPhase() { return crowdMotion.x + uCrowdTime * crowdMotion.y * 6.8; }
vec3 umrahPose(vec3 p) {
  float phase = umrahPhase(), side = _umrah_gait.x, part = _umrah_gait.y, h = _umrah_gait.z;
  if (part > 1.5 && part < 2.5) {
    float weight=clamp((.27*h-p.y)/(.15*h),0.0,1.0);
    p.z -= .23*h*sin(phase*side)*weight;
    p.y += .075*h*max(0.0,cos(phase*side))*weight;
  }
  if (part > 2.5 && part < 3.5) { p.y -= 1.40*h; p.zy = umrahRotate(p.zy, .28*sin(phase*side)*.65); p.y += 1.40*h; }
  if (part > 4.5) p.z -= .012*h*sin(phase)*clamp((.96*h-p.y)/(.7*h),0.0,1.0);
  return p;
}
vec3 umrahNormal(vec3 n) {
  float phase=umrahPhase(), side=_umrah_gait.x, part=_umrah_gait.y;
  if (part>2.5 && part<3.5) n.zy=umrahRotate(n.zy,.28*sin(phase*side)*.65);
  return normalize(n);
}
`;
  function animateMaterial(material, clock) {
    material.onBeforeCompile = shader => {
      shader.uniforms.uCrowdTime = clock;
      shader.vertexShader = shader.vertexShader.replace('#include <common>', '#include <common>\n' + vertex)
        .replace('#include <beginnormal_vertex>', '#include <beginnormal_vertex>\nobjectNormal = umrahNormal(objectNormal);')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\ntransformed = umrahPose(transformed);');
    };
    material.customProgramCacheKey = () => 'umrah-gait-v2';
    return material;
  }
  return { animateMaterial };
});
