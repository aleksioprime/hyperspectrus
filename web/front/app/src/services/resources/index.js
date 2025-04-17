import { UserResource } from "./user.resource";
import { AuthResource } from "./auth.resource";
import { PatientResource } from "./patient.resource";
import { SessionResource } from "./session.resource";
import { RawImageResource } from "./rawImage.resource";
import { DeviceResource } from "./device.resource";
import { SpectrumResource } from "./spectrum.resource";

export default {
    user: new UserResource(),
    auth: new AuthResource(),
    patient: new PatientResource(),
    session: new SessionResource(),
    rawImage: new RawImageResource(),
    device: new DeviceResource(),
    spectrum: new SpectrumResource(),
};