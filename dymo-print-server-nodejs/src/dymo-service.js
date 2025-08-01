const axios = require('axios');
const logger = require('./logger');
const config = require('./config');

class DymoService {
  constructor() {
    this.serviceUrl = config.dymo.serviceUrl;
    this.isConnected = false;
    this.availablePrinters = [];
    this.selectedPrinter = config.print.printerName;
  }

  /**
   * Check if DYMO Label Software is running and accessible
   */
  async checkConnection() {
    try {
      const response = await axios.get(`${this.serviceUrl}/DYMO/DLS/Printing/StatusConnected`, {
        timeout: 5000
      });
      
      this.isConnected = response.data === 'true';
      
      if (this.isConnected) {
        await this.updateAvailablePrinters();
        logger.dymo.connected(this.availablePrinters);
      } else {
        logger.dymo.disconnected();
      }
      
      return this.isConnected;
    } catch (error) {
      this.isConnected = false;
      logger.dymo.error(error);
      return false;
    }
  }

  /**
   * Get list of available DYMO printers
   */
  async updateAvailablePrinters() {
    try {
      const response = await axios.get(`${this.serviceUrl}/DYMO/DLS/Printing/GetPrinters`, {
        timeout: 5000
      });
      
      if (response.data) {
        // Parse XML response to extract printer names
        const printerMatches = response.data.match(/<Name>(.*?)<\/Name>/g);
        this.availablePrinters = printerMatches 
          ? printerMatches.map(match => match.replace(/<\/?Name>/g, ''))
          : [];
      }
      
      return this.availablePrinters;
    } catch (error) {
      logger.dymo.error(error);
      this.availablePrinters = [];
      return [];
    }
  }

  /**
   * Check if selected printer is available
   */
  isPrinterAvailable() {
    return this.isConnected && this.availablePrinters.includes(this.selectedPrinter);
  }

  /**
   * Generate label XML for vial label
   */
  generateVialLabelXml(labelData) {
    const {
      batch_name = '',
      batch_id = '',
      vial_number = '',
      location = '',
      position = '',
      date_created = ''
    } = labelData;

    // Simple DYMO label XML template for 30252 Address Labels (1-1/8" x 3-1/2")
    return `<?xml version="1.0" encoding="utf-8"?>
<DieCutLabel Version="8.0" Units="twips">
  <PaperOrientation>Landscape</PaperOrientation>
  <Id>Address</Id>
  <PaperName>30252 Address</PaperName>
  <DrawCommands>
    <RoundRectangle X="0" Y="0" Width="1581" Height="5040" Rx="270" Ry="270" />
  </DrawCommands>
  <ObjectInfo>
    <TextObject>
      <Name>BATCH_NAME</Name>
      <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
      <BackColor Alpha="0" Red="255" Green="255" Blue="255" />
      <LinkedObjectName></LinkedObjectName>
      <Rotation>Rotation0</Rotation>
      <IsMirrored>False</IsMirrored>
      <IsVariable>True</IsVariable>
      <HorizontalAlignment>Left</HorizontalAlignment>
      <VerticalAlignment>Middle</VerticalAlignment>
      <TextFitMode>ShrinkToFit</TextFitMode>
      <UseFullFontHeight>True</UseFullFontHeight>
      <Verticalized>False</Verticalized>
      <StyledText>
        <Element>
          <String>${batch_name}</String>
          <Attributes>
            <Font Family="Arial" Size="10" Bold="True" Italic="False" Underline="False" Strikeout="False" />
            <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
          </Attributes>
        </Element>
      </StyledText>
    </TextObject>
    <Bounds X="70" Y="140" Width="1441" Height="350" />
  </ObjectInfo>
  <ObjectInfo>
    <TextObject>
      <Name>BATCH_ID</Name>
      <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
      <BackColor Alpha="0" Red="255" Green="255" Blue="255" />
      <LinkedObjectName></LinkedObjectName>
      <Rotation>Rotation0</Rotation>
      <IsMirrored>False</IsMirrored>
      <IsVariable>True</IsVariable>
      <HorizontalAlignment>Left</HorizontalAlignment>
      <VerticalAlignment>Middle</VerticalAlignment>
      <TextFitMode>ShrinkToFit</TextFitMode>
      <UseFullFontHeight>True</UseFullFontHeight>
      <Verticalized>False</Verticalized>
      <StyledText>
        <Element>
          <String>${batch_id} - Vial ${vial_number}</String>
          <Attributes>
            <Font Family="Arial" Size="12" Bold="True" Italic="False" Underline="False" Strikeout="False" />
            <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
          </Attributes>
        </Element>
      </StyledText>
    </TextObject>
    <Bounds X="70" Y="490" Width="1441" Height="420" />
  </ObjectInfo>
  <ObjectInfo>
    <TextObject>
      <Name>LOCATION</Name>
      <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
      <BackColor Alpha="0" Red="255" Green="255" Blue="255" />
      <LinkedObjectName></LinkedObjectName>
      <Rotation>Rotation0</Rotation>
      <IsMirrored>False</IsMirrored>
      <IsVariable>True</IsVariable>
      <HorizontalAlignment>Left</HorizontalAlignment>
      <VerticalAlignment>Middle</VerticalAlignment>
      <TextFitMode>ShrinkToFit</TextFitMode>
      <UseFullFontHeight>True</UseFullFontHeight>
      <Verticalized>False</Verticalized>
      <StyledText>
        <Element>
          <String>${location}</String>
          <Attributes>
            <Font Family="Arial" Size="8" Bold="False" Italic="False" Underline="False" Strikeout="False" />
            <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
          </Attributes>
        </Element>
      </StyledText>
    </TextObject>
    <Bounds X="70" Y="910" Width="1441" Height="280" />
  </ObjectInfo>
  <ObjectInfo>
    <TextObject>
      <Name>POSITION</Name>
      <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
      <BackColor Alpha="0" Red="255" Green="255" Blue="255" />
      <LinkedObjectName></LinkedObjectName>
      <Rotation>Rotation0</Rotation>
      <IsMirrored>False</IsMirrored>
      <IsVariable>True</IsVariable>
      <HorizontalAlignment>Left</HorizontalAlignment>
      <VerticalAlignment>Middle</VerticalAlignment>
      <TextFitMode>ShrinkToFit</TextFitMode>
      <UseFullFontHeight>True</UseFullFontHeight>
      <Verticalized>False</Verticalized>
      <StyledText>
        <Element>
          <String>Position: ${position}</String>
          <Attributes>
            <Font Family="Arial" Size="8" Bold="False" Italic="False" Underline="False" Strikeout="False" />
            <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
          </Attributes>
        </Element>
      </StyledText>
    </TextObject>
    <Bounds X="70" Y="1190" Width="900" Height="280" />
  </ObjectInfo>
  <ObjectInfo>
    <TextObject>
      <Name>DATE</Name>
      <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
      <BackColor Alpha="0" Red="255" Green="255" Blue="255" />
      <LinkedObjectName></LinkedObjectName>
      <Rotation>Rotation0</Rotation>
      <IsMirrored>False</IsMirrored>
      <IsVariable>True</IsVariable>
      <HorizontalAlignment>Right</HorizontalAlignment>
      <VerticalAlignment>Middle</VerticalAlignment>
      <TextFitMode>ShrinkToFit</TextFitMode>
      <UseFullFontHeight>True</UseFullFontHeight>
      <Verticalized>False</Verticalized>
      <StyledText>
        <Element>
          <String>${date_created}</String>
          <Attributes>
            <Font Family="Arial" Size="7" Bold="False" Italic="False" Underline="False" Strikeout="False" />
            <ForeColor Alpha="255" Red="0" Green="0" Blue="0" />
          </Attributes>
        </Element>
      </StyledText>
    </TextObject>
    <Bounds X="970" Y="1190" Width="541" Height="280" />
  </ObjectInfo>
</DieCutLabel>`;
  }

  /**
   * Print label using DYMO service
   */
  async printLabel(labelData) {
    if (!this.isPrinterAvailable()) {
      throw new Error(`Printer "${this.selectedPrinter}" is not available`);
    }

    try {
      const labelXml = this.generateVialLabelXml(labelData);
      
      const response = await axios.post(
        `${this.serviceUrl}/DYMO/DLS/Printing/PrintLabel`,
        {
          printerName: this.selectedPrinter,
          printParamsXml: '',
          labelXml: labelXml,
          labelSetXml: ''
        },
        {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 10000
        }
      );

      if (response.status === 200) {
        return { success: true, message: 'Label printed successfully' };
      } else {
        throw new Error(`Print request failed with status: ${response.status}`);
      }
    } catch (error) {
      logger.dymo.error(error);
      throw error;
    }
  }

  /**
   * Get printer status information
   */
  async getPrinterStatus() {
    return {
      isConnected: this.isConnected,
      availablePrinters: this.availablePrinters,
      selectedPrinter: this.selectedPrinter,
      isPrinterAvailable: this.isPrinterAvailable(),
      serviceUrl: this.serviceUrl
    };
  }

  /**
   * Start periodic connection checking
   */
  startHealthCheck() {
    // Initial check
    this.checkConnection();
    
    // Periodic checks
    setInterval(() => {
      this.checkConnection();
    }, config.dymo.checkInterval);
  }
}

module.exports = DymoService;