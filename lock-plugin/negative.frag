#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec4 redTint;
};
layout(binding = 1) uniform sampler2D source;
void main() {
    vec4 pixel = texture(source, qt_TexCoord0);
    float chroma = max(max(pixel.r, pixel.g), pixel.b) - min(min(pixel.r, pixel.g), pixel.b);
    vec3 negative = vec3(1.0) - pixel.rgb;
    // Near-neutral pixels invert to white/grey; keep those red-toned instead.
    float brightness = dot(pixel.rgb, vec3(0.2126, 0.7152, 0.0722));
    vec3 redFault = redTint.rgb * (0.27 + 0.65 * brightness);
    vec3 faultColor = mix(redFault, negative, smoothstep(0.12, 0.20, chroma));
    float opacity = pixel.a * qt_Opacity;
    fragColor = vec4(faultColor * opacity, opacity);
}
